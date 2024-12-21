from pathlib import Path

import boto3
from boto3.s3.transfer import S3Transfer
from loguru import logger
from vlmrs.schema import BaseModelSchema

from vlmlflow.common import extract_file_info
from vlmlflow.settings.settings import settings


def upload_weights_file(weights_path: Path, model_name: str, model_version: str, bucket_name: str) -> bool:
    """
    Uploads a converted weights file to the specified model name and version in the "mlflow-artifacts-converted" S3 bucket.

    Args:
        weights_path (str): The path to the weights file to upload.
        model_name (str): The name of the model.
        model_version (str): The version of the model.
        bucket_name (str): The name of the S3 bucket.

    Returns:
        bool True if the file was uploaded successfully, False otherwise.

    Side Effects:
        Uploads the weights file to the specified model name and version in the "mlflow-artifacts-converted" S3 bucket.

    """
    s3_client = boto3.client("s3", endpoint_url=settings.mlflow_s3_endpoint_url)

    logger.info("Upload converted weights for model {}, version {}: Start", model_name, model_version)
    transfer = S3Transfer(s3_client)
    transfer.upload_file(
        str(weights_path),
        bucket_name,
        f"{model_name}/{model_version}/{weights_path.name}",
    )
    logger.success(
        "Upload converted weights for model {}, version {}: Сompleted Successfully", model_name, model_version
    )
    return True


def push_converted_weights(
    model_schema: BaseModelSchema, weights_path: Path, force_push_converted_weights: bool
) -> bool:
    """
    Pushes the converted ONNX/TensorRT weights for a given model to the S3 bucket.

    Args:
        model_schema (BaseModelSchema): The schema of the model containing information about the model name, version, and the path to the converted weights file.
        weights_path (Path): The path to the converted weights file.
        force_push_converted_weights (bool): If True, the converted weights will be pushed even if they already exist in the S3 bucket.

    Returns:
        bool: True if the converted weights were successfully pushed to the S3 bucket, False otherwise.

    Raises:
        None

    Side Effects:
        Uploads the converted ONNX/TensorRT weights file to the S3 bucket.

    """

    model_name = model_schema.name
    model_version = model_schema.version

    if not weights_path.exists():
        logger.error("Converted weights file does not exist: {}", weights_path)
        return False

    s3_client = boto3.client("s3", endpoint_url=settings.mlflow_s3_endpoint_url)
    model_list_objects = s3_client.list_objects(
        Bucket=settings.artifacts_converted_bucket, Prefix=f"{model_name}/{model_version}"
    )
    matching_files = extract_file_info(model_list_objects, str(weights_path.name))

    # если файлы с таким именем уже есть и force_push_converted_weights = False, то не пушим
    if matching_files and not force_push_converted_weights:
        logger.warning(
            "Converted weights with such name {} already uploaded! "
            "Skip! If reloading is required, use the "
            "force_push_converted_weights = True parameter",
            weights_path.name,
        )
        logger.warning("Matching files: {}", matching_files)
        return True

    return upload_weights_file(weights_path, model_name, model_version, settings.artifacts_converted_bucket)
