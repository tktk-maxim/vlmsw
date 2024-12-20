from pathlib import Path
from typing import Iterable, Optional

import boto3
import httpx
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


def get_all_models_with_versions() -> dict[str, list[str]]:
    """
    Fetches a list of all available models with their versions.

    This function retrieves the names of all models and their corresponding versions
    from the service.

    :return: A list of dictionaries containing model names and their versions.
    """
    pass


def fetch_model_version_files(model: str, version: str, client: httpx.Client) -> list[str]:
    """
    Fetches the list of available files for a specific model version.

    This function uses the global HTTP client to send a GET request to retrieve
    the files associated with a model version.

    :param model: The name or identifier of the model.
    :param version: The version of the model for which files are requested.
    :param client: The HTTP client used to make the request.
    :return: A list of files associated with the model and version.
    :raises Exception: If the model or version does not exist.
    """
    pass


async def pull(model: str, version: str, save_to: str | Path, file_list: list[str] | None = None) -> bool:
    """
    Pulls a model from the service and saves it to the specified destination path.
    Optionally, only specific files can be pulled if a file list is provided.


    :param model: The name or identifier of the model.
    :param version: The version of the model to pull.
    :param save_to: The directory where the model will be stored.
    :param file_list: A list of specific files to pull. If None, the entire model is pulled.
    :return: True if the model are successfully downloaded, False otherwise.
    :raises Exception: If the model or version does not exist or if the destination path is invalid.
    """
    pass


async def push(model: str, source_path: str | Path, version: str | None = None) -> bool:
    """
    Pushes a model to the service, optionally specifying a version.
    If no version is provided, the model will be pushed to the latest version.

    The function expects a directory or a file path containing the model data to be pushed.

    :param model: The name or identifier of the model.
    :param source_path: The path to the model data. This can be a directory or a file containing the model.
    :param version: The version of the model to push (optional). If None, pushes to the latest version.
    :return: The status of the push operation.
    :raises Exception: If the model or version is invalid, or if there is an issue reading the model data from the source path.
    """
    pass


async def get_converted_files(model: str, version: str) -> list[str]:
    """
    Gets the list of converted files for a specific model and version.

    :param model: The name or identifier of the model.
    :param version: The version of the model.
    :return: A list of converted files associated with the model version.
    :raises Exception: If the model or version does not exist or there is an issue fetching the files.
    """


async def pull_converted_file(model: str, version: str, weight_file_name: str, save_to: str | Path) -> bool:
    """
    Pulls a converted file by its name from the service and saves it to the specified destination path.

    :param model: The name or identifier of the model.
    :param version: The version of the model.
    :param weight_file_name: The name of the converted file to pull.
    :param save_to: The directory where the model will be stored.
    :raises Exception: If the model, version, or file is invalid or there is an issue fetching the file.
    :return: True if the converted file is successfully downloaded, False otherwise.
    """


async def push_converted_file(model: str, version: str, weight_file_name: str, weight_file_path: str | Path) -> bool:
    """
    Uploads a converted file to the service and associates it with a specific model version.

    :param model: The name or identifier of the model.
    :param version: The version of the model to upload the file to.
    :param weight_file_name: The name of the converted file to upload.
    :param weight_file_path: The path to the converted file on the local machine.
    :return: The status of the upload operation.
    :raises Exception: If the model, version, or file is invalid or there is an issue uploading the file.
    """
