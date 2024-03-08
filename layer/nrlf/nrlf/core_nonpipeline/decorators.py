import json
import sys
from functools import wraps
from typing import Callable, Dict, Optional, Type, TypeVar, Union

import boto3
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from lambda_utils.header_config import ConnectionMetadata
from pydantic import BaseModel

from nrlf.core_nonpipeline.common_steps import parse_headers
from nrlf.core_nonpipeline.config import Config
from nrlf.core_nonpipeline.dynamodb.repository import DocumentPointerRepository
from nrlf.core_nonpipeline.errors import OperationOutcomeResponse
from nrlf.core_nonpipeline.logger import logger

RequestParameters = TypeVar("RequestParameters", bound=BaseModel)
RequestBody = TypeVar("RequestBody", bound=BaseModel)

BasicRequestHandler = Callable[..., Dict[str, str]]
RequestHandlerWithParams = Callable[
    [APIGatewayProxyEvent, LambdaContext, ConnectionMetadata, RequestParameters],
    Dict[str, str],
]

DYNAMODB_RESOURCE = boto3.resource("dynamodb")
CONFIG = Config()


def request_handler(
    params: Optional[Type[RequestParameters]] = None,
    body: Optional[Type[RequestBody]] = None,
    skip_parse_headers: bool = False,
    repository: Union[
        Type[DocumentPointerRepository], None
    ] = DocumentPointerRepository,
) -> Callable[[BasicRequestHandler], BasicRequestHandler]:
    def wrapped_func(func: BasicRequestHandler) -> BasicRequestHandler:
        @wraps(func)
        @logger.inject_lambda_context
        @event_source(data_class=APIGatewayProxyEvent)
        def wrapper(*args, **kwargs):
            try:
                event: APIGatewayProxyEvent = args[0]
                context: LambdaContext = args[1]

                kwargs["event"] = event
                kwargs["context"] = context
                kwargs["config"] = CONFIG

                if not skip_parse_headers:
                    kwargs["metadata"] = parse_headers(event.headers)

                if params is not None:
                    kwargs["params"] = params.parse_obj(
                        event.query_string_parameters or {}
                    )

                if body is not None:
                    kwargs["body"] = body.parse_raw(event.body or "{}")

                if repository is not None:
                    kwargs["repository"] = repository(
                        dynamodb=DYNAMODB_RESOURCE, environment_prefix=CONFIG.PREFIX
                    )

                return func(**kwargs)

            except OperationOutcomeResponse as exc:
                return exc.response

            except Exception as exc:
                logger.exception(
                    "An unhandled exception occurred whilst processing the request",
                    exc_info=sys.exc_info(),
                    stacklevel=5,
                )
                operation_outcome = {
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "exception",
                            "diagnostics": str(exc),
                            "coding": [
                                {
                                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                                    "code": "INTERNAL_SERVER_ERROR",
                                    "display": "Internal Server Error",
                                }
                            ],
                        }
                    ],
                }

                return {
                    "statusCode": "500",
                    "body": json.dumps(operation_outcome, indent=2),
                }

        return wrapper

    return wrapped_func
