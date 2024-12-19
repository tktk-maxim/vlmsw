from dotenv import load_dotenv
from loguru import logger
from pydantic import SecretStr
from pydantic_settings import BaseSettings

load_dotenv(".env")


class Settings(BaseSettings):
    """Settings"""

    aws_access_key_id: SecretStr
    aws_secret_access_key: SecretStr
    mlflow_tracking_username: SecretStr
    mlflow_tracking_password: SecretStr
    aws_default_region: str = "k8s00-local"
    mlflow_url: str = "https://mlflow.vizorlabs.ru"
    mlflow_s3_endpoint_url: str = "https://minio.vizorlabs.ru"
    mlflow_default_bucket: str = "mlflow-default"
    artifacts_converted_bucket: str = "mlflow-artifacts-converted"

    class ConfigDict:
        """
        ConfigDict
        """

        extra = "ignore"


settings: Settings = Settings()
logger.info("settings: {}", settings)
