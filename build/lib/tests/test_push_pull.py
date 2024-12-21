import tempfile
from pathlib import Path

import pytest
from vlmrs.models.abobclassifier import AbobClassifierSchema
from vlmrs.models.alpha_pose import AlphaPoseSchema
from vlmrs.models.mmclassifier import MMClassifierSchema
from vlmrs.models.mmocr import MMOcrSchema
from vlmrs.models.mmrotate import MMRotateSchema
from vlmrs.models.mmsegmentation import MMSegmentationSchema
from vlmrs.models.ssd_mobilenetv2 import SSDMobileNetV2Schema
from vlmrs.models.yolov5 import YoloV5Schema
from vlmrs.models.yolov7 import YoloV7Schema
from vlmrs.models.yolov8 import YoloV8Schema
from vlmrs.schema import ShapeModel

from vlmlflow.pull import pull, pull_converted
from vlmlflow.push import push
from vlmlflow.push_converted_weights import push_converted_weights

from . import SchemaFixture


@pytest.mark.parametrize(
    "model_schema",
    [
        {"schema": SSDMobileNetV2Schema, "shape": ShapeModel(channels=3, height=512, width=512)},
        {"schema": AbobClassifierSchema, "shape": ShapeModel(channels=3, height=512, width=512)},
        {"schema": MMClassifierSchema, "shape": ShapeModel(channels=3, height=512, width=512)},
        {"schema": MMSegmentationSchema, "shape": ShapeModel(channels=3, height=512, width=512)},
        {"schema": MMRotateSchema, "shape": ShapeModel(channels=3, height=512, width=512)},
        {"schema": MMOcrSchema, "shape": ShapeModel(channels=3, height=512, width=512)},
        {"schema": AlphaPoseSchema},
        {"schema": YoloV5Schema, "shape": ShapeModel(channels=3, height=640, width=640)},
        {"schema": YoloV7Schema, "shape": ShapeModel(channels=3, height=640, width=640)},
        {"schema": YoloV8Schema, "shape": ShapeModel(channels=3, height=640, width=640)},
    ],
    indirect=True,
)
def test__push__artifacts_schemas(create_artifacts_structure, model_schema) -> None:
    """
    Тест проверяет, что функция push()
    запушит артефакты моделей по схемам
    и после pull() количество артефактов будет совпадать.
    """

    schema_fixture: SchemaFixture = model_schema

    # создать артефакты
    create_artifacts_structure(schema_fixture.schema)

    files_in_dir_before = list(schema_fixture.schema.artifacts_path.iterdir())
    # проверить, что нет пропущенных артефактов
    assert schema_fixture.schema.validate_artifacts()

    # запушить артефакты в mlflow
    push(model_schema=schema_fixture.schema)

    with tempfile.TemporaryDirectory() as tmpdirname:
        schema_fixture.schema.root_dir = Path(tmpdirname)
        schema_fixture.schema.artifacts_path.mkdir(parents=True, exist_ok=True)
        # скачать веса
        artifacts_names = [field_info.default for field_info in schema_fixture.schema.artifacts.model_fields.values()]
        pull(model_schema=schema_fixture.schema, specific_names=artifacts_names)
        files_in_dir = list(schema_fixture.schema.artifacts_path.iterdir())
        assert len(files_in_dir) == len(files_in_dir_before)


def test__pull__only_base_yolov5(create_artifacts_structure) -> None:
    """
    Тест проверяет, что функция pull() с параметром only_base_artifacts=True скачивает
    только базовые артефакты модели YoloV5Schema.
    """

    with tempfile.TemporaryDirectory() as tmpdirname:
        schema = YoloV5Schema(
            name="yolov5_test_base_artifacts",
            version="1",
            shape=ShapeModel(height=640, width=640, batch=1),
            root_dir=Path(tmpdirname),
        )
        create_artifacts_structure(schema)
        # проверить, что нет пропущенных артефактов
        assert schema.validate_artifacts()

        # запушить артефакты в mlflow
        push(model_schema=schema)
        artifacts_names = [field_info.default for field_info in schema.artifacts.model_fields.values()]
        for artifact_name in artifacts_names:
            artifact_path = schema.artifacts_path / artifact_name
            artifact_path.unlink()
        assert len(list(schema.artifacts_path.iterdir())) == 0

        # скачать веса
        pull(model_schema=schema, only_base_artifacts=True)

        assert Path(tmpdirname).exists()

        # Проверка, что в директории только weights и meta
        files_in_dir = list(schema.artifacts_path.iterdir())
        assert len(files_in_dir) == 2
        for base_attribute_name in schema.artifacts.base_attributes.values():
            assert schema.artifacts_path / base_attribute_name in files_in_dir


def test__push_pull_converted__yolov5() -> None:
    """
    Тест проверяет, что функция push_converted_trt_weights загрузит, а pull_converted скачает
    веса модели YoloV5Schema, конвертированные в TensorRT.
    """
    schema = YoloV5Schema(
        name="yolov5_test_converted",
        version="1",
        shape=ShapeModel(height=640, width=640, batch=8),
        compute_capability="8.6",
        cuda_version="11.7",
        trt_version="8.4.3",
    )
    with tempfile.TemporaryDirectory() as tmpdirname:
        schema.root_dir = Path(tmpdirname)
        schema.artifacts_path.mkdir(parents=True, exist_ok=True)
        schema.converted_trt_weights_path.touch()

        push_converted_weights(
            model_schema=schema, weights_path=schema.converted_trt_weights_path, force_push_converted_weights=False
        )
        schema.converted_trt_weights_path.unlink()
        assert not schema.converted_trt_weights_path.exists()
    with tempfile.TemporaryDirectory() as tmpdirname:
        # скачать веса
        pull_converted(
            model_dir=Path(tmpdirname),
            model_name=schema.name,
            model_version=schema.version,
            weights_file_name=schema.converted_trt_weights_name,
        )
        # Проверка, что веса скачаны
        tmpdirname_path = Path(tmpdirname)
        dowloaded_weights_path = tmpdirname_path / schema.converted_trt_weights_name
        assert tmpdirname_path.exists()
        assert dowloaded_weights_path.exists()
        # Проверка, что в директории только trt_weights_path
        files_in_dir = list(tmpdirname_path.iterdir())
        assert len(files_in_dir) == 1 and files_in_dir[0] == dowloaded_weights_path


@pytest.mark.parametrize(
    "model_schema",
    [
        {"schema": YoloV5Schema, "shape": ShapeModel(channels=3, height=640, width=640), "weights_type": "trt"},
        {"schema": YoloV5Schema, "shape": ShapeModel(channels=3, height=640, width=640), "weights_type": "onnx"},
    ],
    indirect=True,
)
def test__pull_converted_weights_name_yolov5__trt_onnx(create_artifacts_structure, model_schema) -> None:
    """
    Тест проверяет, что функция push_converted_weights загрузит, а push_converted_weights скачает
    веса модели YoloV5Schema, конвертированные в TensorRT и ONNX.
    """

    schema_fixture: SchemaFixture = model_schema

    create_artifacts_structure(schema_fixture.schema)
    # проверить, что нет пропущенных артефактов
    assert schema_fixture.schema.validate_artifacts()
    # запушить артефакты в mlflow
    push(model_schema=schema_fixture.schema)
    # удалить директорию с артефактами
    artifacts_names = [field_info.default for field_info in schema_fixture.schema.artifacts.model_fields.values()]
    for artifact_name in artifacts_names:
        artifact_path = schema_fixture.schema.artifacts_path / artifact_name
        artifact_path.unlink()
    assert len(list(schema_fixture.schema.artifacts_path.iterdir())) == 0

    # создать во временной директории сконвертированные веса TensorRT / ONNX
    with tempfile.TemporaryDirectory() as tmpdirname:
        schema_fixture.schema.root_dir = Path(tmpdirname)
        schema_fixture.schema.artifacts_path.mkdir(parents=True, exist_ok=True)
        Path(schema_fixture.schema.artifacts_path, schema_fixture.converted_weights_name).touch()

        # запушить сконвертированные веса в mlflow и S3
        push_converted_weights(
            model_schema=schema_fixture.schema,
            weights_path=schema_fixture.schema.artifacts_path / schema_fixture.converted_weights_name,
            force_push_converted_weights=False,
        )

    with tempfile.TemporaryDirectory() as tmpdirname:
        # скачать сконвертированные веса
        # pull(model_schema=schema_fixture.schema, converted_weights_name=schema_fixture.converted_weights_name)
        # скачать веса
        tmpdirname_path = Path(tmpdirname)

        pull_converted(
            model_dir=tmpdirname_path,
            model_name=schema_fixture.schema.name,
            model_version=schema_fixture.schema.version,
            weights_file_name=schema_fixture.converted_weights_name,
        )

        dowloaded_weights_path = tmpdirname_path / schema_fixture.converted_weights_name
        assert tmpdirname_path.exists()
        # assert dowloaded_weights_path.exists()
        # Проверка, что в директории c артефактами только dowloaded_weights_path (скачанные конвертированные веса)
        files_in_dir = list(tmpdirname_path.iterdir())
        assert len(files_in_dir) == 1 and files_in_dir[0] == dowloaded_weights_path
