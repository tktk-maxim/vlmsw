from typing import Any

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from vlmlflow.settings.settings import settings


def extract_file_info(objects_response: dict[str, Any], keyword: str) -> list[dict[str, Any]]:
    """
    Extract file information from the S3 list objects response based on a keyword.

    Args:
        objects_response (dict[str, Any]): The response from S3 list objects.
        keyword (str): The keyword to search for in the object keys.

    Returns:
        List[Dict[str, Any]]: A list of objects that match the keyword.
    """
    if "Contents" not in objects_response:
        return []

    matching_files = [
        {"Key": obj["Key"], "LastModified": obj["LastModified"], "Size": obj["Size"]}
        for obj in objects_response["Contents"]
        if keyword in obj["Key"]
    ]
    return matching_files


def is_bucket_exists(bucket_name: str) -> bool:
    """
    Checks if a bucket exists.

    Args:
        bucket_name (str): The name of the bucket.

    Returns:
        bool: True if the bucket exists, False otherwise.
    """
    s3 = boto3.resource("s3", endpoint_url=settings.mlflow_s3_endpoint_url)
    return s3.Bucket(bucket_name) in s3.buckets.all()


def create_s3_bucket(bucket_name: str) -> bool:
    """
    Creates a new S3 bucket.

    Args:
        bucket_name (str): The name of the bucket to create.

    Returns:
        None: If the bucket already exists or was created successfully.
        bool: True if the bucket was created successfully, False otherwise.
    """
    # Проверяем существование бакета
    if is_bucket_exists(bucket_name):
        return True

    # Создаем клиента S3
    s3 = boto3.client(
        service_name="s3", region_name=settings.aws_default_region, endpoint_url=settings.mlflow_s3_endpoint_url
    )

    # Создаем бакет
    try:
        s3.create_bucket(
            Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": settings.aws_default_region}
        )
        logger.info("Bucket {} created successfully.", bucket_name)
        return True
    except ClientError as err:
        logger.error("Error creating bucket: {}", err)
    return False
