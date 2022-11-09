from datetime import datetime
from decimal import Decimal
from inspect import signature
from ipaddress import IPv4Network
from logging import getLogger

import pytest
from lambda_pipeline.types import PipelineData
from lambda_utils.constants import LoggingConstants
from lambda_utils.errors import LoggingError
from lambda_utils.logging_utils import (
    _convert_args_to_kwargs,
    _json_encoder,
    duration_in_milliseconds,
    function_handler,
    generate_transaction_id,
    json_encode_message,
)
from nrlf.core.errors import ItemNotFound
from pydantic import BaseModel


def test_generate_transaction_id_unique():
    uuid = generate_transaction_id()
    assert uuid != generate_transaction_id()


def test__convert_args_to_kwargs():
    def f(a, b, c):
        pass

    args = ("A",)
    kwargs = {"b": "B", "c": "C"}
    fn_signature = signature(f)

    _kwargs = _convert_args_to_kwargs(
        fn_signature=fn_signature, args=args, kwargs=kwargs
    )

    assert _kwargs == {"a": "A", "b": "B", "c": "C"}


class PydanticModel(BaseModel):
    a: str


@pytest.mark.parametrize(
    ["obj", "result"],
    [
        (PydanticModel(a="A"), {"a": "A"}),
        (PipelineData(a="A"), {"a": "A"}),
        (IPv4Network("153.191.142.98"), "153.191.142.98/32"),
        (datetime(day=1, month=1, year=1), "0001-01-01T00:00:00"),
        (TypeError("blah"), "TypeError: blah"),
        ({"a": "A"}, {"a": "A"}),
    ],
)
def test__json_encoder(obj, result):
    assert _json_encoder(obj) == result


def test_duration_in_milliseconds():
    assert duration_in_milliseconds(start_seconds=102.1, end_seconds=203.4) == 101300.0


def test_json_encode_message_success():
    json_encode_message({"a": "A"}) == '{"a": "A"}'


def test_json_encode_message_failure():
    with pytest.raises(LoggingError):
        json_encode_message(Decimal("1.02"))


def raise_(ex):
    raise ex("blah")


@pytest.mark.parametrize(
    ["fn", "expected_result", "expected_outcome", "expected_call_stack"],
    [
        (lambda *args, **kwargs: True, True, "SUCCESS", None),
        (
            lambda *args, **kwargs: raise_(ItemNotFound),
            ItemNotFound("blah"),
            "FAILURE",
            None,
        ),
        (
            lambda *args, **kwargs: raise_(TypeError),
            TypeError("blah"),
            "ERROR",
            "Traceback (most recent call last)",
        ),
    ],
)
def test_function_handler(fn, expected_result, expected_outcome, expected_call_stack):
    result, outcome, call_stack = function_handler(fn=fn, args=(), kwargs={})
    assert json_encode_message(result) == json_encode_message(expected_result)
    assert outcome == expected_outcome
    if expected_call_stack:
        assert call_stack.startswith(expected_call_stack)
