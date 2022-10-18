from contextlib import contextmanager

import boto3
import moto
import pytest
from nrlf.core.dynamodb_types import (
    DynamoDbType,
    convert_dynamo_value_to_raw_value,
    convert_value_to_dynamo_format,
)
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data

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
    ["python_type", "value", "expected"],
    (
        [str, "foo", {"S": "foo"}],
        [int, 1, {"N": "1"}],
        [float, 2.3, {"N": "2.3"}],
        [dict, {"foo": {"bar": "123"}}, {"M": {"foo": {"M": {"bar": {"S": "123"}}}}}],
        [list, ["foo", "bar"], {"L": [{"S": "foo"}, {"S": "bar"}]}],
        [type(None), None, {"NULL": True}],
    ),
)
def test_converting_to_dynamodb_type(python_type, value, expected):
    obj = DynamoDbType[python_type](value=value)
    id = DynamoDbType[str](value="my_id")

    assert obj.dict() == expected

    item = {"id": id.dict(), "obj": obj.dict()}
    table_name = "dummy_table"
    with dynamodb_table(table_name=table_name) as client:
        client.put_item(TableName=table_name, Item=item)
        response = client.get_item(TableName=table_name, Key={"id": id.dict()})
        _item = response["Item"]
        _obj = DynamoDbType[python_type].construct(value=_item["obj"])
        assert _item == item
        assert _obj == obj


@pytest.mark.parametrize(
    ["python_type", "value", "expected"],
    (
        [str, {"S": "foo"}, "foo"],
        [int, {"N": "1"}, 1],
        [float, {"N": "2.3"}, 2.3],
        [dict, {"M": {"foo": {"M": {"bar": {"S": "123"}}}}}, {"foo": {"bar": "123"}}],
        [list, {"L": [{"S": "foo"}, {"S": "bar"}]}, ["foo", "bar"]],
        [type(None), {"NULL": True}, None],
    ),
)
def test_converting_dynamodb_to_raw_value(python_type, value, expected):
    obj = DynamoDbType[python_type].construct(value=value)
    raw_value = convert_dynamo_value_to_raw_value(obj)
    assert raw_value == expected


def test_converting_test_doc_to_dynamodb_type():
    fhir_json = read_test_data("nrlf")
    dynamodb_json = read_test_data("nrlf-dynamodb-format")
    assert convert_value_to_dynamo_format(fhir_json) == dynamodb_json


def test_converting_test_doc_from_dynamodb_type():
    fhir_json = read_test_data("nrlf")
    dynamodb_json = read_test_data("nrlf-dynamodb-format")
    assert convert_dynamo_value_to_raw_value(dynamodb_json) == fhir_json
