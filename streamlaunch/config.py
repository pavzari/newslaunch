import os
from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv


@dataclass
class Config:
    GUARDIAN_API_KEY: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    KINESIS_REGION_NAME: str
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    HTTP_REQ_TIMEOUT: int


# the OS environment variables will take precedence over the .env file
def get_config() -> Config:
    load_dotenv()
    return Config(
        GUARDIAN_API_KEY=os.environ["GUARDIAN_API_KEY"],
        AWS_ACCESS_KEY_ID=os.environ["AWS_ACCESS_KEY_ID"],
        AWS_SECRET_ACCESS_KEY=os.environ["AWS_SECRET_ACCESS_KEY"],
        KINESIS_REGION_NAME=os.environ.get("KINESIS_REGION_NAME", "eu-west-2"),
        LOG_LEVEL=os.environ.get("LOG_LEVEL", "INFO"),
        HTTP_REQ_TIMEOUT=int(os.environ.get("HTTP_REQ_TIMEOUT", 10)),
    )
