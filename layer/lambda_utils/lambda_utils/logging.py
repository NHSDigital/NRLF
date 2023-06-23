from enum import Enum
from functools import partial, wraps
from inspect import signature
from logging import Logger as CoreLogger
from logging import getLevelName
from timeit import default_timer as timer
from typing import Any, Callable, Optional, TypeVar, Union

from aws_lambda_powertools import Logger as AwsLogger
from lambda_utils.constants import LoggingConstants, LoggingOutcomes, LogLevel
from lambda_utils.header_config import LoggingHeader
from lambda_utils.logging_utils import (
    CustomFormatter,
    duration_in_milliseconds,
    filter_visible_function_arguments,
    function_handler,
    generate_transaction_id,
    json_encode_message,
)
from pydantic import BaseModel, Extra, Field
from typing_extensions import ParamSpec

from nrlf.core.model import APIGatewayProxyEventModel, Authorizer
from nrlf.core.transform import make_timestamp


class LogTemplateBase(BaseModel):
    correlation_id: str
    nhsd_correlation_id: str
    request_id: str
    transaction_id: str
    host: str
    environment: str
    index: str
    source: str


class LogData(BaseModel):
    inputs: dict[str, object]
    result: Optional[object]


class LogTemplate(LogTemplateBase):
    caller: Union[str, None]  # Identity of the caller
    root: Union[str, None]  # The id of root object that triggered the request
    subject: Union[
        str, None
    ]  # The id of the object being operated on, which normally matches the root but can be a child.
    log_level: str
    log_reference: str
    outcome: str
    duration_ms: int
    message: str
    function: str
    data: LogData
    error: Union[Exception, str, None]
    call_stack: str = None
    timestamp: str = Field(default_factory=make_timestamp)
    sensitive: bool = True

    class Config:
        arbitrary_types_allowed = True  # For Exception
        extra = Extra.forbid

    def dict(self, redact=False, **kwargs):
        """Force exclude_none, allow redaction of field `data`"""
        kwargs["exclude_none"] = True
        log = super().dict(**kwargs)
        if redact and self.sensitive:
            log["data"] = LoggingConstants.REDACTED
        return log

    def json(self, **kwargs):
        """Force exclude_none"""
        kwargs["exclude_none"] = True
        return super().json(**kwargs)


class MinimalRequestContextForLogging(BaseModel):
    accountId: str
    authorizer: Optional[Authorizer] = Field(default_factory=Authorizer)


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


class Logger(AwsLogger, CoreLogger):
    def __init__(
        self,
        *,
        logger_name: str,
        aws_lambda_event: MinimalEventModelForLogging,
        aws_environment: str,
        splunk_index: str,
        source: str,
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
            index=splunk_index,
            source=source,
            transaction_id=self.transaction_id,
        )
        super().__init__(
            logger_name, level="DEBUG", logger_formatter=CustomFormatter(), **kwargs
        )

    @property
    def base_message(self) -> LogTemplate:
        return self._base_message


RT = TypeVar("RT")  # for forwarding type-hints of the return type
P = ParamSpec("P")  # for forwarding type-hints of the decorated kw/args


def log_action(
    *,
    log_reference: Enum,
    log_level: LogLevel = LogLevel.INFO,
    log_fields: list[str] = [],
    log_result: bool = True,
    sensitive: bool = True,
    errors_only: bool = False,
    scope_fn: Union[Callable[P, dict[str, str]], None] = None,
) -> Callable[[Callable[P, RT]], Callable[P, RT]]:
    """
    Args:
        log_reference:  Enum mapping to a verbose description of what this
                        function is doing.
        log_level:      Enum indicating which logging level to be used if the
                        operation successfully completes.  Failed operations
                        will be logged as LogLevel.Error
        log_fields:     Fields to explicitly include. If not provided then no
                        fields are included in the log output.
        log_result:     Indicate whether or not to log the function result.
        level:          logging level for this log.
        sensitive:      Flag for Splunk to categorise this log as sensitive.
        errors_only:    Indicates that successful operations should not be
                        logged, only errors.
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

            data = {
                "inputs": function_kwargs,
            }
            if log_result:
                data["result"] = result

            level = LogLevel.ERROR if outcome == LoggingOutcomes.ERROR else log_level
            error = result if outcome == LoggingOutcomes.ERROR else None

            if not errors_only or level == LogLevel.ERROR:
                scoped_values = {} if scope_fn is None else scope_fn(*args, **kwargs)
                _message = LogTemplate(
                    log_reference=log_reference.name,
                    message=log_reference.value,
                    function=f"{fn.__module__}.{fn.__name__}",
                    data=data,
                    error=error,
                    call_stack=call_stack,
                    outcome=outcome,
                    duration_ms=duration_ms,
                    log_level=getLevelName(level),
                    sensitive=sensitive,
                    **logger.base_message.dict(),
                    **scoped_values,
                )
                message_dict = _message.dict()
                message_json = json_encode_message(message=message_dict)
                logger.log(msg=message_json, level=level)

            if isinstance(result, Exception):
                raise result
            return result

        return wrapper

    return decorator


def make_scoped_log_action(
    scope_fn,
    *args,
    **kwargs,
):
    """
    Uses a partial to define the request scoped values once, rather than each
    @log_action.
    """
    _kwargs: dict[str, Any] = {**kwargs}
    _kwargs["scope_fn"] = scope_fn
    return partial(log_action, *args, **_kwargs)
