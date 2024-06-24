import sys

from nrlf.core.config import Config
from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.logger import LogReference, logger
from nrlf.core.response import Response


@request_handler(skip_request_verification=True)
def handler(event, context) -> Response:
    """
    Retrieves the status of the API.

    Returns:
        Response: The response object containing the status code and body.
    """
    try:
        logger.log(LogReference.STATUS000)
        logger.log(LogReference.STATUS001)
        config = Config()

        logger.log(LogReference.STATUS002)
        repository = DocumentPointerRepository(environment_prefix=config.PREFIX)
        repository.get_by_id("ODSX-NULL")

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
