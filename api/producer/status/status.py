import sys

import boto3

from nrlf.core.config import Config
from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.logger import LogReference, logger
from nrlf.core.response import Response


@request_handler(skip_request_verification=True)
def handler(event, context) -> Response:
    """
    Entrypoint for the status function
    """
    try:
        logger.log(LogReference.STATUS000)
        logger.log(LogReference.STATUS001)
        config = Config()

        logger.log(LogReference.STATUS002)
        repository = DocumentPointerRepository(
            dynamodb=boto3.resource("dynamodb"), environment_prefix=config.PREFIX
        )
        repository.get("D#NULL")

        response = Response(statusCode="200", body="OK")
        logger.log(LogReference.STATUS999)

        return response

    except Exception as exc:
        logger.log(
            LogReference.STATUS003,
            error=str(exc),
            exc_info=sys.exc_info(),
            stacklevel=5,
        )

        return Response(statusCode="503", body="Service unavailable")
