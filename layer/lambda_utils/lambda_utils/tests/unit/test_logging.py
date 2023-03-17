import json
import logging
from enum import Enum
from tempfile import NamedTemporaryFile

import pytest
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_utils.logging import Logger, log_action
from lambda_utils.tests.unit.utils import make_aws_event
from nrlf.core.errors import DynamoDbError
from nrlf.core.validators import validate_timestamp


class LogReference(Enum):
    HELLO001 = "Hello, world!"


LOGGER_NAME = __name__

DUMMY_LOGGER_KWARGS = {
    "aws_lambda_event": APIGatewayProxyEventModel(
        **make_aws_event(
            headers={
                "x-correlation-id": "123",
                "nhsd-correlation-id": "456",
                "x-request-id": "789",
            }
        )
    ),
    "transaction_id": "ABC",
    "aws_environment": "TEST",
}


def _standard_test(fn):

    with NamedTemporaryFile() as temp_file:
        logger = Logger(
            logger_name=temp_file.name,
            logger_handler=logging.FileHandler(temp_file.name),
            **DUMMY_LOGGER_KWARGS
        )

        # Result unaffected by log decorator
        result = fn(foo="abc", bar="def", logger=logger)
        assert result == "abcdef"

        # Process the log
        message = json.loads(temp_file.read())

    # Validate the time components
    timestamp = message.pop("timestamp")
    duration_ms = message.pop("duration_ms")
    validate_timestamp(timestamp)
    assert duration_ms >= 0

    return message


@pytest.mark.parametrize(
    ["log_fields", "expected_data_inputs"],
    [
        (None, {}),
        (["foo", "bar"], {"foo": "abc", "bar": "def"}),
        (["foo"], {"foo": "abc"}),
        (["bar"], {"bar": "def"}),
        ([], {}),
    ],
)
def test_log_with_log_fields_filter(log_fields, expected_data_inputs):
    kwargs = {"log_fields": log_fields} if log_fields is not None else {}

    @log_action(log_reference=LogReference.HELLO001, **kwargs)
    def _dummy_function(foo: str, bar: str):
        return foo + bar

    message = _standard_test(fn=_dummy_function)
    assert message == {
        "correlation_id": "123",
        "nhsd_correlation_id": "456",
        "transaction_id": "ABC",
        "request_id": "789",
        "log_level": "INFO",
        "log_reference": "HELLO001",
        "outcome": "SUCCESS",
        "message": "Hello, world!",
        "data": {
            "function": "test_logging._dummy_function",
            "result": "abcdef",
            "inputs": expected_data_inputs,
        },
        "environment": "TEST",
        "host": "123456789012",
        "sensitive": True,
    }


@pytest.mark.parametrize(
    ["error", "outcome", "result", "expected_log_level"],
    [
        (DynamoDbError, "FAILURE", "DynamoDbError: An error message", "INFO"),
        (TypeError, "ERROR", "TypeError: An error message", "ERROR"),
    ],
)
def test_log_with_error_outcomes(error, outcome, result, expected_log_level):
    @log_action(log_reference=LogReference.HELLO001, log_fields=["foo", "bar"])
    def _dummy_function(foo: str, bar: str):
        raise error("An error message")

    with NamedTemporaryFile() as temp_file:
        logger = Logger(
            logger_name=temp_file.name,
            logger_handler=logging.FileHandler(temp_file.name),
            **DUMMY_LOGGER_KWARGS
        )

        # Result unaffected by log decorator
        with pytest.raises(error):
            _dummy_function(foo="abc", bar="def", logger=logger)

        # Process the log
        message = json.loads(temp_file.read())

    # Validate the time components
    timestamp = message.pop("timestamp")
    duration_ms = message.pop("duration_ms")
    validate_timestamp(timestamp)
    assert duration_ms >= 0

    if outcome == "ERROR":
        assert message.pop("call_stack").startswith("Traceback (most recent call last)")
        assert message.pop("error") == message["data"]["result"]

    assert message == {
        "correlation_id": "123",
        "nhsd_correlation_id": "456",
        "transaction_id": "ABC",
        "request_id": "789",
        "log_level": expected_log_level,
        "log_reference": "HELLO001",
        "outcome": outcome,
        "message": "Hello, world!",
        "data": {
            "function": "test_logging._dummy_function",
            "result": result,
            "inputs": {"foo": "abc", "bar": "def"},
        },
        "environment": "TEST",
        "host": "123456789012",
        "sensitive": True,
    }
