from functools import wraps
from inspect import signature
from logging import getLevelName
from timeit import default_timer as timer
from typing import Any, Callable, Optional, TypeVar, Union

from aws_lambda_powertools import Logger as _Logger
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_utils.constants import LoggingOutcomes, LogLevel
from lambda_utils.header_config import LoggingHeader
from lambda_utils.logging_utils import (
    CustomFormatter,
    duration_in_milliseconds,
    filter_visible_function_arguments,
    function_handler,
    generate_transaction_id,
    json_encode_message,
)
from nrlf.core.transform import make_timestamp
from pydantic import BaseModel, Field
from typing_extensions import ParamSpec


class LogTemplateBase(BaseModel):
    correlation_id: str
    nhsd_correlation_id: str
    request_id: str
    transaction_id: str
    host: str
    environment: str

    class Config:
        arbitrary_types_allowed = True


class LogTemplate(LogTemplateBase):
    log_level: str
    log_reference: str
    outcome: str
    duration_ms: int
    message: str
    data: dict
    error: Union[Exception, str, None]
    call_stack: str = None
    timestamp: str = None
    sensitive: bool = True

    class Config:
        arbitrary_types_allowed = True


class MinimalRequestContextForLogging(BaseModel):
    accountId: str


class MinimalEventModelForLogging(APIGatewayProxyEventModel):
    headers: dict[str, str]
    requestContext: MinimalRequestContextForLogging
    # Internal flag
    is_default_event: bool = Field(default=False, allow_mutation=True)
    # Force 'optional' the following fields
    resource: Optional[Any]
    path: Optional[Any]
    httpMethod: Optional[Any]
    multiValueHeaders: Optional[Any]
    isBase64Encoded: Optional[Any]


def prepare_default_event_for_logging() -> MinimalEventModelForLogging:
    uid = f"<no-logging-credentials-provided>-{generate_transaction_id()}"
    logging_headers = LoggingHeader(
        **{"x-correlation-id": uid, "x-request-id": uid, "nhsd-correlation-id": uid}
    )
    return MinimalEventModelForLogging(
        headers=logging_headers.dict(by_alias=True),
        requestContext=MinimalRequestContextForLogging(accountId=uid),
    )


class Logger(_Logger):
    def __init__(
        self,
        *,
        logger_name: str,
        aws_lambda_event: MinimalEventModelForLogging,
        aws_environment: str,
        transaction_id: str = None,
        **kwargs,
    ):
        headers = aws_lambda_event.dict().get("headers", {})
        logging_header = LoggingHeader(**headers)

        self.transaction_id = transaction_id or generate_transaction_id()
        self._base_message = LogTemplateBase(
            **logging_header.dict(),
            host=aws_lambda_event.requestContext.accountId,
            environment=aws_environment,
            transaction_id=self.transaction_id,
        )
        super().__init__(logger_name, logger_formatter=CustomFormatter(), **kwargs)

    @property
    def base_message(self) -> LogTemplate:
        return self._base_message


RT = TypeVar("RT")  # for forwarding type-hints of the return type
P = ParamSpec("P")  # for forwarding type-hints of the decorated kw/args


def log_action(
    *,
    narrative: str,
    log_fields: list[str] = [],
    log_result: bool = True,
    sensitive: bool = True,
) -> Callable[[Callable[P, RT]], Callable[P, RT]]:
    """
    Args:
        narrative:  Verbose description of what this function is doing.
        log_fields: Fields to explicitly include. If not provided then
                    no fields are included in the log output.
        log_result: Indicate whether or not to log the function result.
        level:      logging level for this log.
        sensitive:  Flag for Splunk to categorise this log as sensitive.
    """

    def decorator(fn: Callable[P, RT]) -> Callable[P, RT]:
        @wraps(fn)
        def wrapper(*args: P.args, logger: Logger = None, **kwargs: P.kwargs) -> RT:
            if logger is None:
                return fn(*args, **kwargs)

            fn_signature = signature(fn)
            if "logger" in fn_signature.parameters:
                kwargs["logger"] = logger

            start_seconds = timer()
            result, outcome, call_stack = function_handler(fn, args, kwargs)
            duration_ms = duration_in_milliseconds(
                start_seconds=start_seconds, end_seconds=timer()
            )

            function_kwargs = filter_visible_function_arguments(
                fn_signature=fn_signature,
                function_args=args,
                function_kwargs=kwargs,
                log_fields=log_fields,
            )

            data = {"inputs": function_kwargs}
            if log_result:
                data["result"] = result

            level = (
                LogLevel.ERROR if outcome == LoggingOutcomes.ERROR else LogLevel.INFO
            )
            error = result if outcome == LoggingOutcomes.ERROR else None
            _message = LogTemplate(
                log_reference=f"{fn.__module__}.{fn.__name__}",
                message=narrative,
                data=data,
                error=error,
                call_stack=call_stack,
                outcome=outcome,
                duration_ms=duration_ms,
                log_level=getLevelName(level),
                timestamp=make_timestamp(),
                sensitive=sensitive,
                **logger.base_message.dict(),
            )

            message_dict = _message.dict(exclude_none=True)
            message_json = json_encode_message(message=message_dict)
            logger.log(msg=message_json, level=level)

            if isinstance(result, Exception):
                raise result
            return result

        return wrapper

    return decorator
