import collections
import json
import traceback
from datetime import datetime
from inspect import Signature
from ipaddress import IPv4Network
from uuid import uuid4

from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter
from lambda_utils.constants import LoggingConstants, LoggingOutcomes
from lambda_utils.errors import LoggingError
from pydantic import BaseModel

from nrlf.core.errors import ERROR_SET_4XX


def generate_transaction_id() -> str:
    return str(uuid4())


class CustomFormatter(LambdaPowertoolsFormatter):
    def serialize(self, log: dict) -> str:
        return self.json_serializer(log["message"])


def _convert_args_to_kwargs(fn_signature: Signature, args: tuple, kwargs: dict) -> dict:
    result = dict(kwargs)
    for arg_value, arg_name in zip(args, fn_signature.parameters):
        result[arg_name] = arg_value
    return result


def _json_encoder(obj: any) -> str:
    if isinstance(obj, BaseModel):
        return obj.dict()
    elif isinstance(obj, collections.abc.Mapping):
        return dict(obj)
    elif isinstance(obj, IPv4Network):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Exception):
        return f"{type(obj).__name__}: {str(obj)}"
    elif callable(obj):
        return obj.__name__
    return json._default_encoder.encode(obj)


def duration_in_milliseconds(start_seconds: float, end_seconds: float) -> int:
    return int((end_seconds - start_seconds) * LoggingConstants.TO_MILLISECONDS)


def filter_visible_function_arguments(
    fn_signature: Signature,
    function_args: tuple,
    function_kwargs: dict,
    log_fields: list[str],
):
    function_kwargs = _convert_args_to_kwargs(
        fn_signature=fn_signature, args=function_args, kwargs=function_kwargs
    )

    function_kwargs = {k: v for k, v in function_kwargs.items() if k in log_fields}

    for field in LoggingConstants.RESERVED_FIELDS:
        function_kwargs.pop(field, None)

    return function_kwargs


def json_encode_message(message: dict, indent=LoggingConstants.JSON_INDENT) -> str:
    try:
        return json.dumps(message, indent=indent, default=_json_encoder)
    except TypeError as e:
        raise LoggingError(f"Logging error: {str(e)}")


def function_handler(fn, args, kwargs) -> tuple[any, str, str]:
    call_stack = None
    try:
        result = fn(*args, **kwargs)
        outcome = LoggingOutcomes.SUCCESS
    except ERROR_SET_4XX as error:  # ToDo - This is not true.  Only 400 when validation on input occurs.  Output validation failure is 500.
        result = error
        outcome = LoggingOutcomes.FAILURE
    except Exception as error:
        result = error
        outcome = LoggingOutcomes.ERROR
        call_stack = traceback.format_exc()
    return result, outcome, call_stack
