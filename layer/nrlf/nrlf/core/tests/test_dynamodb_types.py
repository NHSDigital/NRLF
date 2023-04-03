from contextlib import contextmanager

import boto3
import moto
import pytest
from nrlf.core.dynamodb_types import (
    DynamoDbIntType,
    DynamoDbStringType,
    convert_dynamo_value_to_raw_value,
)
from pydantic import ValidationError

DEFAULT_ATTRIBUTE_DEFINITIONS = [{"AttributeName": "id", "AttributeType": "S"}]
DEFAULT_KEY_SCHEMA = [{"AttributeName": "id", "KeyType": "HASH"}]


@contextmanager
def dynamodb_table(
    table_name: str,
    attribute_definitions: list[dict[str:str]] = DEFAULT_ATTRIBUTE_DEFINITIONS,
    key_schema: list[dict[str:str]] = DEFAULT_KEY_SCHEMA,
):
    with moto.mock_dynamodb():
        client = boto3.client("dynamodb")
        client.create_table(
            AttributeDefinitions=attribute_definitions,
            TableName=table_name,
            KeySchema=key_schema,
            BillingMode="PAY_PER_REQUEST",
        )
        yield client

        client.delete_table(TableName=table_name)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [("1", "1"), ("test", "test")],
)
def test_dynamo_db_string_type_validation_success(input_value, expected_value: str):
    dynamo_db_string = DynamoDbStringType(__root__=input_value)
    assert dynamo_db_string.dict() == {"S": expected_value}


@pytest.mark.parametrize("input_value", [None, 2, True])
def test_dynamo_db_string_type_validation_failure(input_value):
    with pytest.raises(ValidationError):
        _dynamo_db_string = DynamoDbStringType(__root__=input_value)


@pytest.mark.parametrize(
    "input_value,expected_value",
    [(2, "2"), (-1, "-1")],
)
def test_dynamo_db_int_type_validation_success(input_value, expected_value: str):
    dynamo_db_int = DynamoDbIntType(__root__=input_value)
    assert dynamo_db_int.dict() == {"N": expected_value}


@pytest.mark.parametrize(
    "input_value", [None, "1.4", "1.0", "test", "1", 1.3, 2.9, -1.0]
)
def test_dynamo_db_int_type_validation_failure(input_value):
    with pytest.raises(ValidationError):
        _dynamo_db_string = DynamoDbIntType(__root__=input_value)


@pytest.mark.parametrize(
    ["value", "expected"],
    (
        [{"S": "foo"}, "foo"],
        [{"N": "1"}, 1],
        [{"N": "2.3"}, 2.3],
        [{"M": {"foo": {"M": {"bar": {"S": "123"}}}}}, {"foo": {"bar": "123"}}],
        [{"L": [{"S": "foo"}, {"S": "bar"}]}, ["foo", "bar"]],
        [{"NULL": True}, None],
    ),
)
def test_converting_dynamodb_to_raw_value(value, expected):
    raw_value = convert_dynamo_value_to_raw_value(value)
    assert raw_value == expected
