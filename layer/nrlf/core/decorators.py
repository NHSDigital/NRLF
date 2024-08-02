import functools
import inspect
import sys
import warnings
from typing import Any, Callable, Dict, Optional, Type, Union

from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel

from nrlf.core.authoriser import get_pointer_types, parse_permissions_file
from nrlf.core.codes import SpineErrorConcept
from nrlf.core.config import Config
from nrlf.core.constants import (
    NHSD_CORRELATION_ID_HEADER,
    PERMISSION_ALLOW_ALL_POINTER_TYPES,
    X_CORRELATION_ID_HEADER,
    X_REQUEST_ID_HEADER,
    PointerTypes,
)
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


def header_handler(
    wrapped_func: Callable[..., Dict[str, Any]]
) -> Callable[..., Dict[str, Any]]:
    """
    Wraps the function to set the specific headers in the request and response
    """

    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        event: APIGatewayProxyEvent = args[0]

        response = wrapped_func(*args, **kwargs)

        try:
            if "headers" not in response:
                response["headers"] = {}

            echoed_headers = {
                name: event.get_header_value(name)
                for name in [
                    X_REQUEST_ID_HEADER,
                    X_CORRELATION_ID_HEADER,
                ]
                if event.get_header_value(name)
            }
            response["headers"].update(echoed_headers)
        except Exception as exc:
            logger.exception(
                "An error occurred whilst setting response headers",
                exc_info=sys.exc_info(),
                stacklevel=5,
                log_reference=LogReference.ERROR003.name,
            )

        logger.log(
            LogReference.HANDLER016,
            status_code=response["statusCode"],
            headers=response["headers"],
        )

        return response

    return wrapper


def logger_initialiser(
    wrapper_func: Callable[..., Dict[str, Any]]
) -> Callable[..., Dict[str, Any]]:
    """
    Wraps the function and initialises the request logger
    """

    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        event: APIGatewayProxyEvent = args[0]

        correlation_id = event.get_header_value(NHSD_CORRELATION_ID_HEADER)
        if correlation_id:
            logger.set_correlation_id(correlation_id)
        else:
            logger.log(
                LogReference.HANDLER017,
                id_header=NHSD_CORRELATION_ID_HEADER,
                headers=event.headers,
            )

        return wrapper_func(*args, **kwargs)

    return wrapper


RepositoryType = Union[Type[DocumentPointerRepository], None]


def load_connection_metadata(headers: Dict[str, str], config: Config):
    logger.log(LogReference.HANDLER002, headers=headers)
    metadata = parse_headers(headers)
    logger.log(LogReference.HANDLER003, metadata=metadata.dict())
    if PERMISSION_ALLOW_ALL_POINTER_TYPES in metadata.nrl_permissions:
        logger.log(LogReference.HANDLER004a)
        metadata.pointer_types = PointerTypes.list()
        return metadata

    logger.log(LogReference.HANDLER004b)
    pointer_types = parse_permissions_file(metadata)
    if not pointer_types and not metadata.is_test_event:
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


def verify_request_ids(event: APIGatewayProxyEvent):
    caller_request_id = event.get_header_value("x-request-id")
    if not caller_request_id:
        logger.log(LogReference.HANDLER014, headers=event.headers)
        raise OperationOutcomeError(
            status_code="400",
            severity="error",
            code="invalid",
            details=SpineErrorConcept.from_code("MISSING_OR_INVALID_HEADER"),
            diagnostics="The X-Request-Id header is missing or invalid",
        )

    caller_correlation_id = event.get_header_value("nhsd-correlation-id")
    if not caller_correlation_id:
        logger.log(LogReference.HANDLER015, headers=event.headers)
        raise OperationOutcomeError(
            status_code="400",
            severity="error",
            code="invalid",
            details=SpineErrorConcept.from_code("MISSING_OR_INVALID_HEADER"),
            diagnostics="The NHSD-Correlation-Id header is missing or invalid",
        )


def basic_handler(
    event: APIGatewayProxyEvent,
    context: LambdaContext,
    func: RequestHandler,
) -> Dict[str, str]:
    """
    Request handler without any parsing or authorisation checks.
    """
    logger.log(LogReference.HANDLER013)
    response = func(event, context)
    logger.log(
        LogReference.HANDLER999,
        status_code=response.statusCode,
        response=response.dict(),
    )
    return response.dict()


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
                return basic_handler(event, context, func, **kwargs)

            verify_request_ids(event)

            config = Config()
            logger.log(LogReference.HANDLER001, config=config.dict())
            metadata = load_connection_metadata(event.headers, config)

            if metadata.pointer_types == []:
                logger.log(
                    LogReference.HANDLER005,
                    ods_code=metadata.ods_code,
                    pointer_types=metadata.pointer_types,
                )
                raise OperationOutcomeError(
                    status_code="403",
                    severity="error",
                    code="forbidden",
                    details=SpineErrorConcept.from_code("ACCESS DENIED"),
                    diagnostics=f"Your organisation '{metadata.ods_code}' does not have permission to access this resource. Contact the onboarding team.",
                )

            kwargs = {
                "event": event,
                "context": context,
                "config": metadata,
                "metadata": metadata,
                "params": parse_params(params, event.query_string_parameters),
                "body": parse_body(body, event.body),
                "path": parse_path(path, event.path_parameters),
            }

            if repository is not None:
                kwargs["repository"] = repository(table_name=config.TABLE_NAME)

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
            functools.wraps(func),
            error_handler,
            header_handler,
            logger_initialiser,
            event_source(data_class=APIGatewayProxyEvent),
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
