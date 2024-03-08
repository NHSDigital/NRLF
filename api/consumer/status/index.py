from typing import Dict

import boto3
from pydantic import BaseSettings, Field

from nrlf.core_nonpipeline.decorators import DocumentPointerRepository, request_handler


class Config(BaseSettings):
    AWS_REGION: str = Field(default=..., env="AWS_REGION")
    PREFIX: str = Field(default=..., env="PREFIX")
    DYNAMODB_TIMEOUT: float = Field(default=..., env="DYNAMODB_TIMEOUT")


@request_handler(skip_parse_headers=True, repository=None)
def handler(**_) -> Dict[str, str]:
    """
    Entrypoint for the status function
    """
    try:
        config = Config()
        repository = DocumentPointerRepository(
            dynamodb=boto3.resource("dynamodb"), environment_prefix=config.PREFIX
        )

        # Hit the DB
        repository.get("D#NULL")

        return {"statusCode": "200", "body": "OK"}

    except Exception as exc:
        return {"statusCode": "503", "body": "Service Unavailable"}
