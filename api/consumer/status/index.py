import sys

import boto3
from pydantic import BaseSettings, Field

from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.logger import logger
from nrlf.core.response import Response


class Config(BaseSettings):
    AWS_REGION: str = Field(default=..., env="AWS_REGION")
    PREFIX: str = Field(default=..., env="PREFIX")


@request_handler(skip_parse_headers=True, repository=None)
def handler() -> Response:
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

        return Response(
            statusCode="200",
            body="OK",
        )

    except Exception as exc:
        logger.exception(
            "An unhandled exception occurred whilst processing the request",
            exception=str(exc),
            exc_info=sys.exc_info(),
            stacklevel=5,
        )

        return Response(statusCode="503", body="Service unavailable")
