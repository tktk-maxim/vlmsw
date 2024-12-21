from pathlib import Path
from typing import Any, Iterable, Optional

import mlflow
import mlflow.pyfunc
import yaml
from easydict import EasyDict
from loguru import logger
from vlmrs.schema import BaseModelSchema

from vlmlflow.settings.settings import settings


class TruncatedEasyDict(EasyDict):
    """
    A class that represents a dictionary with a maximum number of symbols in a string.
    """

    def __init__(self, *args: Iterable, max_symbols: int = 200, **kwargs: dict):
        """
        Initialize the TruncatedEasyDict object.

        Args:
            *args: The positional arguments.
            max_symbols: The maximum number of symbols in a string.
            **kwargs: The keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.max_symbols = max_symbols

    def __setitem__(self, key: Any, value: Any) -> None:
        """
        Set the value for the given key.

        Args:
            key: The key.
            value: The value.
        """
        if isinstance(value, str) and len(value) > self.max_symbols:
            value = "hidden for log"
        elif isinstance(value, dict):
            value = TruncatedEasyDict(value, max_symbols=self.max_symbols)
        super().__setitem__(key, value)

    def update(self, *args: Any, **kwargs: Any) -> None:
        """
        Update the dictionary with the given arguments.

        Args:
            *args: The positional arguments.
            **kwargs: The keyword arguments.
        """
        other = dict(*args, **kwargs)
        for key, value in other.items():
            self[key] = value

    def setmaxsymbols(self, max_symbols: int) -> None:
        """
        Set the maximum number of symbols in a string.

        Args:
            max_symbols: The maximum number of symbols.
        """
        self.max_symbols = max_symbols


class EmptyModelWrapper(mlflow.pyfunc.PythonModel):
    """
    A class that represents an empty model.
    """

    def load_context(self, context: Any) -> None:
        """
        A description of the entire function, its parameters, and its return types.
        """

    def predict(self, context: Any, model_input: Any) -> None:
        """
        A description of the entire function, its parameters, and its return types.
        """


def log_params(params_path: Path) -> None:
    """
    Logs parameters from a YAML file to MLFlow.

    Args:
        params_path (Path): The path to the YAML file containing the parameters.

    Returns:
        None

    Description:
        This function reads the YAML file specified by `params_path` and parses its contents into a `TruncatedEasyDict` object.
        It then logs each parameter to MLFlow using the `mlflow.log_param` function.
        The parameters are logged with their respective keys and values.
        The function logs a message to the logger before logging the parameters.
    """
    with open(params_path) as fh:
        parsed_params = TruncatedEasyDict(yaml.load(fh, Loader=yaml.FullLoader))
        logger.info("parsed params.yaml: {}", parsed_params)

        for k, v in parsed_params.items():
            mlflow.log_param(k, v)


def push(model_schema: BaseModelSchema, note: Optional[str] = None, skip_missing_optional: bool = True) -> None:
    """
    A function that pushes model artifacts to MLflow, sets up tracking information, starts a new MLflow run,
    logs the model, and provides information about the run and the registered model.

    Parameters:
        model_schema (BaseModelSchema): An instance of the model schema containing information about the model.
        note (Optional[str]): Additional notes to be added to the MLflow run.
        skip_missing_optional (bool): A boolean value indicating whether to skip the logging of optional artifacts.

    Returns:
        None
    """
    model_schema.validate_artifacts()
    artifacts_dict = {}

    # исключить из списка артефактов отсутствующие файлы, которые помечены в схеме как необязательные
    if skip_missing_optional:
        for field_info in model_schema.artifacts.model_fields.values():
            if isinstance(field_info.json_schema_extra, dict) and field_info.json_schema_extra.get(
                "optional_artifact"
            ):
                if not Path(model_schema.artifacts_path / field_info.default).exists():
                    continue
            artifacts_dict[field_info.default] = str(model_schema.artifacts_path / field_info.default)
    else:
        # включить в список артефактов все файлы
        artifacts_dict = {
            field_info.default: str(model_schema.artifacts_path / field_info.default)
            for field_info in model_schema.artifacts.model_fields.values()
        }

    mlflow.set_tracking_uri(settings.mlflow_url)
    client = mlflow.tracking.MlflowClient(tracking_uri=settings.mlflow_url)
    mlflow.set_experiment(model_schema.name)

    with mlflow.start_run(run_name=None) as run:
        # загрузить примечания
        if note:
            client.set_tag(run.info.run_id, "mlflow.note.content", note)

        # логировать параметры
        params = artifacts_dict.get("params")
        if params:
            log_params(model_schema.artifacts_path / model_schema.artifacts.params)

        # логировать артефакты
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=EmptyModelWrapper(),
            artifacts=artifacts_dict,
            registered_model_name=model_schema.name,
        )

        logger.info("Artifacts logged to MLflow run: {}", run.info.run_id)
        logger.info("Model registered with artifact path: {}", model_schema.name)
