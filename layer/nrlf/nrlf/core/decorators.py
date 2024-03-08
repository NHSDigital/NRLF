import functools
import inspect
import sys
import warnings
from functools import wraps
from typing import Callable, Optional, Type, Union

import boto3
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel

from nrlf.core.constants import CONFIG
from nrlf.core.dynamodb.repository import DocumentPointerRepository
from nrlf.core.logger import logger
from nrlf.core.request import parse_headers
from nrlf.core.response import Response

RequestHandler = Callable[..., Response]
DYNAMODB_RESOURCE = boto3.resource("dynamodb")


def error_handler(wrapped_func: RequestHandler) -> RequestHandler:
    """
    Wraps the function in a try/except block and logs any unhandled exceptions
    """

    def wrapper(*args, **kwargs):
        try:
            return wrapped_func(*args, **kwargs)

        except Exception as exc:
            logger.exception(
                "An unhandled exception occurred whilst processing the request",
                exc_info=sys.exc_info(),
                stacklevel=5,
            )

            return Response.from_exception(exc)

    return wrapper


def request_handler(
    params: Optional[Type[BaseModel]] = None,
    body: Optional[Type[BaseModel]] = None,
    skip_parse_headers: bool = False,
    repository: Union[
        Type[DocumentPointerRepository], None
    ] = DocumentPointerRepository,
) -> Callable[[RequestHandler], RequestHandler]:
    """
    Decorator for request handlers.

    Args:
        params (Optional[Type[BaseModel]]): The parameter model to parse query string parameters.
        body (Optional[Type[BaseModel]]): The body model to parse request body.
        skip_parse_headers (bool): Flag to skip parsing request headers. Defaults to False.
        repository (Union[Type[DocumentPointerRepository], None]): The repository class to use. Defaults to DocumentPointerRepository.

    Returns:
        Callable[[RequestHandler], RequestHandler]: The decorated request handler function.
    """

    def wrapped_func(func: RequestHandler) -> RequestHandler:
        def wrapper(*args, **kwargs):
            event: APIGatewayProxyEvent = args[0]
            context: LambdaContext = args[1]

            kwargs["event"] = event
            kwargs["context"] = context
            kwargs["config"] = CONFIG

            if not skip_parse_headers:
                kwargs["metadata"] = parse_headers(event.headers)

            if params is not None:
                kwargs["params"] = params.parse_obj(event.query_string_parameters or {})

            if body is not None:
                kwargs["body"] = body.parse_raw(event.body or "{}")

            if repository is not None:
                kwargs["repository"] = repository(
                    dynamodb=DYNAMODB_RESOURCE, environment_prefix=CONFIG.PREFIX
                )

            function_kwargs = {}

            signature = inspect.signature(func)
            for parameter in signature.parameters.values():
                assert (
                    parameter.name in kwargs
                ), f"Missing parameter {parameter.name} from request handler"
                function_kwargs[parameter.name] = kwargs[parameter.name]

            return func(**function_kwargs)

        decorators = [
            wraps(func),
            logger.inject_lambda_context,
            event_source(data_class=APIGatewayProxyEvent),
            error_handler,
        ]

        return functools.reduce(
            lambda func, decorator: decorator(func), decorators, wrapper
        )

    return wrapped_func


def deprecated(message: str):
    def decorator(func):
        """
        This decorator will result in a warning appearing when used
        """

        @functools.wraps(func)
        def new_func(*args, **kwargs):
            warnings.simplefilter("always", DeprecationWarning)  # turn off filter
            warnings.warn(
                "Call to deprecated function {}. {}".format(func.__name__, message),
                category=DeprecationWarning,
                stacklevel=2,
            )
            warnings.simplefilter("default", DeprecationWarning)  # reset filter
            return func(*args, **kwargs)

        return new_func

    return decorator
