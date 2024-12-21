from dotenv import load_dotenv
from loguru import logger
from pydantic import SecretStr
from pydantic_settings import BaseSettings

load_dotenv(".env")


class Settings(BaseSettings):
    """Settings"""

    MODEL_STORAGE_ENDPOINT: str = "http://localhost:6529/model_versions/get_file/3"


    class ConfigDict:
        """
        ConfigDict
        """

        extra = "ignore"


settings: Settings = Settings()
logger.info("settings: {}", settings)
