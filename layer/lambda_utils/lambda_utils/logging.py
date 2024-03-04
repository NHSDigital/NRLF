from enum import Enum
from functools import partial, wraps
from inspect import signature
from logging import Logger as CoreLogger
from logging import getLevelName
from threading import local
from timeit import default_timer as timer
from traceback import format_exception
from typing import Any, Callable, Literal, Optional, TypeVar, Union

from aws_lambda_powertools import Logger as AwsLogger
from lambda_utils.constants import LoggingConstants, LoggingOutcomes, LogLevel
from lambda_utils.header_config import LoggingHeader
from lambda_utils.logging_utils import (
    CustomFormatter,
    duration_in_milliseconds,
    filter_visible_function_arguments,
    generate_transaction_id,
    json_encode_message,
)
from pydantic import BaseModel, Extra, Field
from typing_extensions import ParamSpec

from nrlf.core.errors import ERROR_SET_4XX
from nrlf.core.model import APIGatewayProxyEventModel, Authorizer
from nrlf.core.transform import make_timestamp

logging_context = local()
logging_context.current_action = None


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
    inputs: Optional[dict[str, object]]
    result: Optional[object] = None
    extra_fields: dict[str, object] = Field(default_factory=dict)


class LogTemplate(LogTemplateBase):
    caller: Optional[str] = None  # Identity of the caller
    root: Optional[str] = None  # The id of root object that triggered the request
    subject: Optional[
        str
    ] = None  # The id of the object being operated on, which normally matches the root but can be a child.
    log_level: str
    log_reference: str
    outcome: str
    duration_ms: int
    message: str
    function: Optional[str] = None
    data: LogData
    error: Union[Exception, str, None] = None
    call_stack: Optional[str] = None
    timestamp: str = Field(default_factory=make_timestamp)
    sensitive: bool = True

    class Config:
        arbitrary_types_allowed = True  # For Exception
        extra = Extra.forbid

    def model_dump(self, redact=False, **kwargs):
        """Force exclude_none, allow redaction of field `data`"""
        kwargs["exclude_none"] = True
        log = super().model_dump(**kwargs)
        if redact and self.sensitive:
            log["data"] = LoggingConstants.REDACTED
        return log

    def model_dump_json(self, **kwargs):
        """Force exclude_none"""
        kwargs["exclude_none"] = True
        return super().model_dump_json(**kwargs)


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
        resource=None,
        path=None,
        httpMethod=None,
        multiValueHeaders=None,
        isBase64Encoded=None,
        headers=logging_headers.model_dump(by_alias=True),
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
        transaction_id: Optional[str] = None,
        **kwargs,
    ):
        headers = aws_lambda_event.dict().get("headers", {})
        logging_header = LoggingHeader(**headers)

        self.transaction_id = transaction_id or generate_transaction_id()
        self._base_message = LogTemplateBase(
            **logging_header.model_dump(),
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
    def base_message(self) -> LogTemplateBase:
        return self._base_message


RT = TypeVar("RT")  # for forwarding type-hints of the return type
P = ParamSpec("P")  # for forwarding type-hints of the decorated kw/args


def log_action(
    *,
    log_reference: Enum,
    log_level: int = LogLevel.INFO,
    log_fields: list[str] = [],
    log_result: bool = True,
    sensitive: bool = True,
    errors_only: bool = False,
    scope_fn: Union[Callable[P, dict[str, str]], None] = None,
    **extra_fields,
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
            with LogAction(
                log_reference=log_reference,
                log_level=log_level,
                sensitive=sensitive,
                errors_only=errors_only,
                logger=logger,
            ) as action:

                error = False
                result = None
                try:
                    result = fn(*args, **kwargs)
                except ERROR_SET_4XX as e:
                    result = e
                    raise
                except Exception as e:
                    error = True
                    result = e
                    raise
                else:
                    return result
                finally:
                    if not errors_only or error or log_level == LogLevel.ERROR:
                        function_kwargs = filter_visible_function_arguments(
                            fn_signature=fn_signature,
                            function_args=args,
                            function_kwargs=kwargs,
                            log_fields=log_fields,
                        )

                        action.add_inputs(**function_kwargs)

                        if log_result:
                            action.set_result(result)

                        scoped_values = (
                            {} if scope_fn is None else scope_fn(*args, **kwargs)
                        )

                        action.override(
                            function=f"{fn.__module__}.{fn.__name__}",
                            **scoped_values,
                        )
                        action.add_fields(**extra_fields)

        return wrapper

    return decorator


class LogAction:
    __old_action: Union["LogAction", None, Literal["unset"]] = "unset"

    def __init__(
        self,
        *,
        log_reference: Enum,
        log_level: int = LogLevel.INFO,
        sensitive: bool = True,
        errors_only: bool = False,
        logger: Union[Logger, None] = None,
        **inputs,
    ):
        self.log_reference = log_reference
        self.log_level = log_level
        self.sensitive = sensitive
        self.errors_only = errors_only
        self.logger = logger
        self.data = {"inputs": inputs, "extra_fields": {}}
        self.overrides = {}

    def add_fields(self, **kwargs):
        self.data["extra_fields"].update(kwargs)

    def override(self, **kwargs):
        self.overrides.update(kwargs)

    def set_result(self, result):
        self.data["result"] = result

    def add_inputs(self, **inputs):
        self.data["inputs"].update(inputs)

    def __enter__(self):
        assert self.__old_action == "unset", "Cannot reuse LogActions"
        self.__old_action = logging_context.current_action

        if self.logger is None:
            logging_context.current_action = None
            return self
        else:
            logging_context.current_action = self

        self.__start_seconds = timer()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logging_context.current_action = self.__old_action

        if self.logger is None:
            return

        duration_ms = duration_in_milliseconds(
            start_seconds=self.__start_seconds, end_seconds=timer()
        )

        level = self.log_level
        call_stack = None
        outcome = LoggingOutcomes.SUCCESS
        error = None
        if isinstance(exc_value, ERROR_SET_4XX):
            outcome = LoggingOutcomes.FAILURE
            self.set_result(exc_value)
        elif isinstance(exc_value, Exception):
            level = LogLevel.ERROR
            call_stack = "".join(format_exception(exc_type, exc_value, traceback))
            outcome = LoggingOutcomes.ERROR
            error = exc_value
            self.set_result(exc_value)

        if not self.errors_only or level == LogLevel.ERROR:
            _message = LogTemplate(
                log_reference=self.log_reference.name,
                message=self.log_reference.value,
                error=error,
                call_stack=call_stack,
                outcome=outcome,
                duration_ms=duration_ms,
                log_level=getLevelName(level),
                sensitive=self.sensitive,
                data=LogData(**self.data),
                **self.logger.base_message.dict(),
                **self.overrides,
            )
            message_dict = _message.dict()
            message_json = json_encode_message(message=message_dict)
            self.logger.log(msg=message_json, level=level)


def add_log_fields(**kwargs):
    if (current_action := logging_context.current_action) is not None:
        logging_context.current_action.add_fields(**kwargs)


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
