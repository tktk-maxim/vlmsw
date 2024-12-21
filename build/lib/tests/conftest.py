import tempfile
from collections import namedtuple
from collections.abc import Iterator
from pathlib import Path

import pytest
from loguru import logger
from vlmrs.schema import BaseModelSchema

from vlmlflow.common import create_s3_bucket
from vlmlflow.settings.settings import settings

from . import SchemaFixture


@pytest.fixture(scope="session", autouse=True)
def init_before_tests_starting():
    # подготовка перед тестами
    bucket_names = [settings.mlflow_default_bucket, settings.artifacts_converted_bucket]
    for bucket_name in bucket_names:
        is_bucket_created = create_s3_bucket(bucket_name)
        assert is_bucket_created, f"bucket: {bucket_name} not created"


@pytest.fixture(scope="function")
def create_artifacts_structure() -> None:
    def _create_artifacts_structure(schema: BaseModelSchema):
        schema.artifacts_path.mkdir(parents=True, exist_ok=True)
        for artifact_name in schema.artifacts.model_dump().values():
            if artifact_name:
                artifact_path = schema.artifacts_path / artifact_name
                artifact_path.touch()

    return _create_artifacts_structure


@pytest.fixture
def model_schema(request) -> Iterator[SchemaFixture]:
    schema_class = request.param["schema"]
    shape = request.param.get("shape")
    name = str(request.param["schema"].__name__)
    weights_type = request.param.get("weights_type")
    version = "1"
    onnx_version = "1.17.0"
    cuda_version = "11.7"
    trt_version = "8.4.3"
    compute_capability = "8.6"

    config_filename = request.param.get("config_filename")
    expected_labels = request.param.get("expected_labels")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger.info("Creating temporary directory for {} at {}", name, tmpdir)
        model_schema_instance = schema_class(
            shape=shape,
            name=name,
            version=version,
            root_dir=Path(tmpdir),
            onnx_version=onnx_version,
            cuda_version=cuda_version,
            trt_version=trt_version,
            compute_capability=compute_capability,
        )

        if weights_type == "onnx":
            converted_weights_name = model_schema_instance.converted_onnx_weights_name
        elif weights_type == "trt":
            converted_weights_name = model_schema_instance.converted_trt_weights_name
        else:
            converted_weights_name = None

        yield SchemaFixture(
            schema=model_schema_instance,
            config_filename=config_filename,
            expected_labels=expected_labels,
            converted_weights_name=converted_weights_name,
        )
