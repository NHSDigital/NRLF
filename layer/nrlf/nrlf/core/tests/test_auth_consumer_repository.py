import json
import time
from contextlib import contextmanager
from copy import deepcopy
from typing import Generator

import boto3
import moto
import pytest
from nrlf.core.errors import DynamoDbError
from nrlf.core.model import AuthConsumer
from nrlf.core.repository import MAX_TRANSACT_ITEMS, Repository, to_kebab_case
from nrlf.core.types import DynamoDbClient

DEFAULT_ATTRIBUTE_DEFINITIONS = [{"AttributeName": "id", "AttributeType": "S"}]
DEFAULT_KEY_SCHEMA = [{"AttributeName": "id", "KeyType": "HASH"}]
TABLE_NAME = to_kebab_case(AuthConsumer.__name__)
API_VERSION = 1
auth_json = {
    "id": "Yorkshire Ambulance Service",
    "application_id": "SCRa",
    "document_types": [
        "https://snomed.info/ict|861421000000109",
        "https://snomed.info/ict|861421000000108",
        "https://snomed.info/ict|861421000000107",
    ],
}


@contextmanager
def mock_dynamodb() -> Generator[DynamoDbClient, None, None]:
    with moto.mock_dynamodb():
        client: DynamoDbClient = boto3.client("dynamodb")
        client.create_table(
            AttributeDefinitions=DEFAULT_ATTRIBUTE_DEFINITIONS,
            TableName=TABLE_NAME,
            KeySchema=DEFAULT_KEY_SCHEMA,
            BillingMode="PAY_PER_REQUEST",
        )
        yield client


def test__table_name_prefix():
    repository = Repository(
        item_type=AuthConsumer, client=None, environment_prefix="foo-bar-"
    )
    assert repository.table_name == "foo-bar-auth-consumer"


def test_create_auth_details():
    model = AuthConsumer(**auth_json)
    with mock_dynamodb() as client:
        repository = Repository(item_type=AuthConsumer, client=client)
        repository.create(item=model)
        response = client.scan(TableName=TABLE_NAME)

    (item,) = response["Items"]
    recovered_item = AuthConsumer(**item)
    assert recovered_item.dict() == model


def test_cant_create_if_item_already_exists():
    model = AuthConsumer(**auth_json)
    with pytest.raises(DynamoDbError), mock_dynamodb() as client:
        repository = Repository(item_type=AuthConsumer, client=client)
        repository.create(item=model)
        repository.create(item=model)


def test_read_auth():
    model = AuthConsumer(**auth_json)
    with mock_dynamodb() as client:
        repository = Repository(item_type=AuthConsumer, client=client)
        repository.create(item=model)
        result = repository.read(
            KeyConditionExpression="id = :id",
            ExpressionAttributeValues={":id": model.id.dict()},
        )
    assert model == result
