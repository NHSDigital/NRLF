from functools import wraps
from inspect import signature
from logging import getLevelName
from timeit import default_timer as timer
from types import FunctionType

from aws_lambda_powertools import Logger as _Logger
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_utils.constants import LoggingOutcomes, LogLevel
from lambda_utils.logging_utils import (
    CustomFormatter,
    duration_in_milliseconds,
    filter_visible_function_arguments,
    function_handler,
    generate_transaction_id,
    json_encode_message,
)
from nrlf.core.transform import make_timestamp
from pydantic import BaseModel


class LogTemplate(BaseModel):
    correlation_id: str = None
    nhsd_correlation_id: str = None
    transaction_id: str = None
    request_id: str = None
    log_level: str = None
    log_reference: str = None
    outcome: str = None
    duration_ms: int = None
    message: str = None
    data: dict = None
    error: Exception = None
    call_stack: str = None
    environment: str = None
    timestamp: str = None
    sensitive: bool = True

    class Config:
        arbitrary_types_allowed = True


class Logger(_Logger):
    def __init__(
        self,
        *,
        logger_name: str,
        aws_lambda_event: APIGatewayProxyEventModel,
        aws_environment: str,
        nrlf_transaction_id: str = None,
        **kwargs,
    ):
        self._base_message = LogTemplate(
            correlation_id=aws_lambda_event.headers["x-correlation-id"],
            nhsd_correlation_id=aws_lambda_event.headers["nhsd-correlation-id"],
            transaction_id=nrlf_transaction_id or generate_transaction_id(),
            request_id=aws_lambda_event.headers["x-request-id"],
            host=aws_lambda_event.requestContext.accountId,
            environment=aws_environment,
        )
        super().__init__(logger_name, logger_formatter=CustomFormatter(), **kwargs)

    @property
    def base_message(self) -> LogTemplate:
        return self._base_message


def log_action(
    *,
    narrative: str,
    log_fields: list[str] = [],
    log_result: bool = True,
    sensitive: bool = True,
):
    """
    Args:
        narrative:  Verbose description of what this function is doing.
        log_fields: Fields to explicitly include. If not provided then
                    no fields are included in the log output.
        log_result: Indicate whether or not to log the function result.
        level:      logging level for this log.
        sensitive:  Flag for Splunk to categorise this log as sensitive.
    """

    def decorator(fn: FunctionType):
        @wraps(fn)
        def wrapper(*args, logger: Logger = None, **kwargs):
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
            )
            message_json = json_encode_message(
                message={
                    **logger.base_message.dict(exclude_none=True),
                    **_message.dict(exclude_none=True),
                }
            )
            logger.log(msg=message_json, level=level)

            if isinstance(result, Exception):
                raise result
            return result

        return wrapper

    return decorator
