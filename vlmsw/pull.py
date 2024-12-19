from pathlib import Path
from typing import Iterable, Optional

import boto3
import mlflow
from botocore.exceptions import BotoCoreError
from loguru import logger
from mlflow.entities import FileInfo
from mlflow.entities.model_registry import ModelVersion
from mlflow.tracking import MlflowClient
from vlmrs.schema import BaseModelSchema

from vlmlflow.common import extract_file_info, is_bucket_exists
from vlmlflow.exceptions import BucketNotFoundException, NotFoundModelException
from vlmlflow.settings.settings import settings


def get_selected_version_model(
    client: mlflow.tracking.MlflowClient, model_name: str, model_version: str
) -> ModelVersion:
    """
    Retrieves the selected version of a model from the given MLflow client.

    Args:
        client (mlflow.tracking.MlflowClient): The MLflow client used to retrieve the model version.
        model_name (str): The name of the model.
        model_version (str): The version of the model.

    Returns:
        mlflow.entities.model_registry.ModelVersion: The selected model version.

    Raises:
        Exception: If there is no model with the given name and version.
    """
    try:
        return client.get_model_version(
            name=model_name,
            version=model_version,
        )
    except mlflow.exceptions.RestException as exc:
        raise NotFoundModelException(f"There is no model {model_name} with version {model_version}. {exc}") from exc


def pull_converted(
    model_dir: Path,
    model_name: str,
    model_version: str,
    weights_file_name: str,
) -> bool:
    """
    Pulls the converted weights for a given model from S3 bucket using the provided model directory,
    model name, model version, and weights file name.

    Args:
        model_dir (Path): The directory where the model weights will be stored.
        model_name (str): The name of the model.
        model_version (str): The version of the model.
        weights_file_name (str): The name of the weights file.

    Returns:
        bool: True if the weights are successfully downloaded, False otherwise.
    """
    if not is_bucket_exists(settings.artifacts_converted_bucket):
        raise BucketNotFoundException("Bucket does not exist!!!")

    s3_client = boto3.client("s3", endpoint_url=settings.mlflow_s3_endpoint_url)

    if not model_dir.exists():
        model_dir.mkdir(parents=True, exist_ok=True)

    model_list_objects = s3_client.list_objects(
        Bucket=settings.artifacts_converted_bucket, Prefix=f"{model_name}/{model_version}"
    )

    matching_files = extract_file_info(model_list_objects, weights_file_name)

    if len(matching_files) > 1:
        logger.error("There are several files with current configuration: {}", matching_files)
        return False

    if not matching_files:
        logger.warning("No converted weights for this configuration !!! weights_file_name: {}", weights_file_name)
        return False

    file = matching_files[0]

    logger.info("Download converted weights: Start. Weights file name: {}", file["Key"])

    try:
        s3_client.download_file(
            Bucket=settings.artifacts_converted_bucket,
            Key=file["Key"],
            Filename=str(model_dir / weights_file_name),
        )
        logger.success("Download converted weights: Сompleted Successfully. Weights file name: {}", file["Key"])
        return True
    except BotoCoreError as e:
        logger.exception("BotoCore error occurred", exc_info=e)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("An unexpected error occurred", exc_info=e)
    return False


def remove_base_weights_from_artifacts(artifacts: Iterable[FileInfo], model_schema: BaseModelSchema) -> list:
    """
    Remove the base weights from the given list of artifacts.

    Parameters:
        artifacts (Iterable[FileInfo]): The list of artifacts.
        model_schema (BaseModelSchema): The model schema containing information about the base artifacts.

    Returns:
        list: The list of artifacts without the base weights.
    """
    return [artifact for artifact in artifacts if Path(artifact.path).name != model_schema.artifacts.weights]


def search_specific_artifacts(artifacts: Iterable[FileInfo], specific_names: Iterable[str]) -> list[FileInfo]:
    """
    Retrieves specific artifacts from a list based on given names.

    Args:
        artifacts (Iterable[FileInfo]): List of artifacts to search.
        specific_names (Iterable[str]): Names of specific artifacts to search for.

    Returns:
        list[FileInfo]: List of specific artifacts found.

    Raises:
        ValueError: If not all specific artifacts are found.
    """
    founded_artifacts = list(filter(lambda art: Path(art.path).name in specific_names, artifacts))

    # проверить, что все артефакты были найдены
    founded_artifacts_set = set(Path(x.path).name for x in founded_artifacts)
    specific_names_set = set(specific_names)

    if not specific_names_set.issubset(founded_artifacts_set):
        raise ValueError(f"Cannot find the following artifacts: {specific_names_set - founded_artifacts_set}")

    return founded_artifacts


def pull(
    model_schema: BaseModelSchema,
    pull_force: bool = False,
    only_base_artifacts: bool = False,
    specific_names: Optional[Iterable[str]] = None,
    # converted_weights_name: Optional[str] = None,
) -> bool:
    """
    Pulls the specified model version and its artifacts from the MLflow server.

    Args:
        model_schema (BaseModelSchema): An instance of the model.
        pull_force (bool, optional): Whether to force the pull even if the artifacts already exist. Defaults to False.
        only_base_artifacts (bool, optional): Whether to only download the base artifacts. Defaults to False.
        specific_names (list[str], optional): A list of specific artifact names to download. Defaults to None.
        # converted_weights_name (str, optional): The name of the converted weights file to download.
        #                                          If provided, the function will check if the file exists in the S3 bucket
        #                                          and download it if it does. Defaults to None.
        #                                          For example: "yolo_result_h640_w640_b1_cc8.6_cuda11.7_trt8.4.3_fp16.engine"

    Returns:
        bool: True if the artifacts were successfully downloaded, False otherwise.

    Raises:
        FileNotFoundError: If the specified model version does not exist.
        Exception: If the specified model version does not match the retrieved model version.

    Notes:
        - This function checks the MLflow environment variables.
        - If the `use_rt_weights` parameter is True, the function downloads the converted TensorRT weights.
        - If the `only_base_artifacts` parameter is True, the function only downloads the base artifacts.
        - If the `specific_names` parameter is provided, the function downloads only the specified artifacts.
        - The function creates the model output directory if it does not exist.
        - The function retrieves the artifacts from the MLflow server.
        - The function downloads the artifacts to the model output directory.
        - If the `pull_force` parameter is False and the artifact already exists, the function skips the download.
    """
    logger.info(
        "name={}, version={}, only_base_artifacts={}, specific_names={}",
        model_schema.name,
        model_schema.version,
        only_base_artifacts,
        specific_names,
    )

    client = MlflowClient(tracking_uri=settings.mlflow_url)

    response_model_version = get_selected_version_model(client, model_schema.name, model_schema.version)
    if response_model_version.version != model_schema.version:
        raise NotFoundModelException(f"There is no version {model_schema.version} for model {model_schema.name}")

    logger.success("Find version: {}, stage: {}", model_schema.version, response_model_version.current_stage)

    model_output_dir = Path(model_schema.root_dir, model_schema.name, model_schema.version)

    # создать директорию для модели, в случае отсутствия
    if not model_output_dir.exists():
        model_output_dir.mkdir(parents=True, exist_ok=True)

    artifact_list = []

    # получить список всех артефактов
    logger.info("Get artifacts from model version: {} from mlflow", model_schema.version)
    artifacts_resp = client.list_artifacts(response_model_version.run_id, model_schema.artifacts_path_suffix)
    logger.success("artifacts_resp: {}", artifacts_resp)

    # получить список только базовых артефактов, отфильтровав остальные
    if only_base_artifacts:
        base_artifacts = model_schema.artifacts.base_attributes.values()
        artifact_list += [
            artifact_resp for artifact_resp in artifacts_resp if Path(artifact_resp.path).name in base_artifacts
        ]

    # если указаны конкретные артефакты, добавить их в список
    if specific_names:
        artifact_list += search_specific_artifacts(artifacts=artifacts_resp, specific_names=specific_names)

    logger.info("result_artifact_list: {}", artifact_list)

    # # загрузить конвертированные веса
    # if not converted_weights_name:
    #     logger.info("skip download converted weights: {}", converted_weights_name)
    # else:
    #     weights_path = model_schema.artifacts_path / converted_weights_name
    #     logger.info("send converted weights path: {}", weights_path)

    #     if pull_force or not weights_path.exists():
    #         if pull_converted(
    #             model_dir=model_schema.artifacts_path,
    #             model_name=model_schema.name,
    #             model_version=model_schema.version,
    #             weights_file_name=converted_weights_name,
    #         ):
    #             artifact_list = remove_base_weights_from_artifacts(artifacts=artifact_list, model_schema=model_schema)
    #     else:
    #         logger.info(
    #             "skip download converted weights: {}. File already exists: {}", converted_weights_name, weights_path
    #         )
    #         artifact_list = remove_base_weights_from_artifacts(artifacts=artifact_list, model_schema=model_schema)

    # скачать артефакты
    for artifact in artifact_list:
        if pull_force or not Path(model_output_dir, artifact.path).exists():
            logger.info("start download artifact: {}", artifact.path)
            local_path = client.download_artifacts(
                response_model_version.run_id, str(artifact.path), str(model_output_dir)
            )
            logger.success("artifact downloaded in: {}", local_path)
        else:
            logger.info(
                "skip download artifact: {}. File already exists: {}", artifact.path, model_output_dir / artifact.path
            )
    return True
