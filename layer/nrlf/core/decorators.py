import functools
import inspect
import sys
import warnings
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union

from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel

from nrlf.core.authoriser import get_pointer_types
from nrlf.core.codes import SpineErrorConcept
from nrlf.core.config import Config
from nrlf.core.dynamodb.repository import DocumentPointerRepository
from nrlf.core.errors import OperationOutcomeError, ParseError
from nrlf.core.logger import LogReference, logger
from nrlf.core.request import parse_body, parse_headers, parse_params, parse_path
from nrlf.core.response import Response

RequestHandler = Callable[..., Response]


def error_handler(
    wrapped_func: Callable[..., Dict[str, Any]],
) -> Callable[..., Dict[str, Any]]:
    """
    Wraps the function in a try/except block and logs any unhandled exceptions
    """

    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            return wrapped_func(*args, **kwargs)

        except OperationOutcomeError as exc:
            response = exc.response.dict(exclude_none=True)
            logger.log(LogReference.ERROR001, error=str(exc), response=response)
            return response

        except ParseError as exc:
            response = exc.response.dict(exclude_none=True)
            logger.log(LogReference.ERROR002, error=str(exc), response=response)
            return response

        except Exception as exc:
            response = Response.from_exception(exc).dict(exclude_none=True)
            logger.exception(
                "An unhandled exception occurred whilst processing the request",
                exc_info=sys.exc_info(),
                stacklevel=5,
                log_reference=LogReference.ERROR000.name,
                response=response,
            )
            return response

    return wrapper


RepositoryType = Union[Type[DocumentPointerRepository], None]


def load_connection_metadata(headers: Dict[str, str], config: Config):
    logger.log(LogReference.HANDLER002, headers=headers)
    metadata = parse_headers(headers)
    logger.log(LogReference.HANDLER003, metadata=metadata.dict())

    if metadata.enable_authorization_lookup:
        logger.log(LogReference.HANDLER004)
        pointer_types = get_pointer_types(metadata, config)
        metadata.pointer_types = pointer_types

    return metadata


def filter_kwargs(handler_func: RequestHandler, kwargs: Dict[str, Any]):
    function_kwargs = {}
    signature = inspect.signature(handler_func)
    for parameter in signature.parameters.values():
        if parameter.name in kwargs:
            function_kwargs[parameter.name] = kwargs[parameter.name]

    logger.log(
        LogReference.HANDLER012,
        original_kwargs_keys=kwargs.keys(),
        filtered_kwargs_keys=function_kwargs.keys(),
    )
    return function_kwargs


def request_handler(
    params: Optional[Type[BaseModel]] = None,
    body: Optional[Type[BaseModel]] = None,
    path: Optional[Type[BaseModel]] = None,
    repository: RepositoryType = DocumentPointerRepository,
    skip_request_verification: bool = False,
) -> Callable[[RequestHandler], Callable[..., Dict[str, str]]]:
    """
    Decorator for request handlers.

    Args:
        params (Optional[Type[BaseModel]]): The parameter model to parse query string parameters.
        body (Optional[Type[BaseModel]]): The body model to parse request body.
        skip_parse_headers (bool): Flag to skip parsing request headers. Defaults to False.
        repository (Union[Type[DocumentPointerRepository], None]): The repository class to use.

    Returns:
        Callable[[RequestHandler], RequestHandler]: The decorated request handler function.
    """

    def wrapped_func(func: RequestHandler):
        def wrapper(*args, **kwargs):
            event: APIGatewayProxyEvent = args[0]
            context: LambdaContext = args[1]

            logger.log(
                code=LogReference.HANDLER000,
                method=event.http_method,
                path=event.path,
                headers=event.headers,
            )

            if skip_request_verification:
                logger.log(LogReference.HANDLER013)
                response = func(event, context)
                logger.log(
                    LogReference.HANDLER999,
                    status_code=response.statusCode,
                    response=response.dict(),
                )
                return response.dict()

            kwargs["event"] = event
            kwargs["context"] = context
            kwargs["config"] = Config()
            logger.log(LogReference.HANDLER001, config=kwargs["config"].dict())

            kwargs["metadata"] = load_connection_metadata(
                event.headers, kwargs["config"]
            )

            if kwargs["metadata"].pointer_types == []:
                logger.log(
                    LogReference.HANDLER005,
                    ods_code=kwargs["metadata"].ods_code,
                    pointer_types=kwargs["metadata"].pointer_types,
                )
                raise OperationOutcomeError(
                    status_code="403",
                    severity="error",
                    code="forbidden",
                    details=SpineErrorConcept.from_code("ACCESS DENIED"),
                    diagnostics=f"Your organisation '{kwargs['metadata'].ods_code}' does not have permission to access this resource. Contact the onboarding team.",
                )

            if params is not None:
                logger.log(
                    LogReference.HANDLER006,
                    params=event.query_string_parameters,
                    model=params.__name__,
                )
                kwargs["params"] = parse_params(params, event.query_string_parameters)
                logger.log(
                    LogReference.HANDLER007, parsed_params=kwargs["params"].dict()
                )

            if body is not None:
                logger.log(
                    LogReference.HANDLER008, body=event.body, model=body.__name__
                )
                kwargs["body"] = parse_body(body, event.body)
                logger.log(LogReference.HANDLER009, parsed_body=kwargs["body"].dict())

            if path is not None:
                logger.log(
                    LogReference.HANDLER010,
                    path=event.path_parameters,
                    model=path.__name__,
                )
                kwargs["path"] = parse_path(path, event.path_parameters)
                logger.log(LogReference.HANDLER011, parsed_path=kwargs["path"].dict())

            if repository is not None:
                kwargs["repository"] = repository(
                    environment_prefix=kwargs["config"].PREFIX,
                )

            function_kwargs = filter_kwargs(func, kwargs)

            logger.log(LogReference.HANDLER013)
            response = func(**function_kwargs)
            logger.log(
                LogReference.HANDLER999,
                status_code=response.statusCode,
                response=response.dict(),
            )
            return response.dict()

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
                f"Call to deprecated function {func.__name__}. {message}",
                category=DeprecationWarning,
                stacklevel=2,
            )
            warnings.simplefilter("default", DeprecationWarning)  # reset filter
            return func(*args, **kwargs)

        return new_func

    return decorator
