import json
import time
from contextlib import contextmanager
from copy import deepcopy
from typing import Generator

import boto3
import moto
import pytest
from botocore.exceptions import ClientError
from nrlf.core.errors import DynamoDbError, ItemNotFound, TooManyItemsError
from nrlf.core.model import Auth, DocumentPointer
from nrlf.core.query import hard_delete_query, update_and_filter_query
from nrlf.core.repository import (
    MAX_TRANSACT_ITEMS,
    Repository,
    handle_dynamodb_errors,
    to_kebab_case,
)
from nrlf.core.transform import (
    create_document_pointer_from_fhir_json as _create_document_pointer_from_fhir_json,
)
from nrlf.core.transform import (
    update_document_pointer_from_fhir_json as _update_document_pointer_from_fhir_json,
)
from nrlf.core.types import DynamoDbClient
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data

DEFAULT_ATTRIBUTE_DEFINITIONS = [{"AttributeName": "id", "AttributeType": "S"}]
DEFAULT_KEY_SCHEMA = [{"AttributeName": "id", "KeyType": "HASH"}]
TABLE_NAME = to_kebab_case(Auth.__name__)
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
    repository = Repository(item_type=Auth, client=None, environment_prefix="foo-bar-")
    assert repository.table_name == "foo-bar-auth"


def test_create_auth_details():
    model = Auth(**auth_json)
    with mock_dynamodb() as client:
        repository = Repository(item_type=Auth, client=client)
        repository.create(item=model)
        response = client.scan(TableName=TABLE_NAME)

    (item,) = response["Items"]
    recovered_item = Auth(**item)
    assert recovered_item.dict() == model


def test_cant_create_if_item_already_exists():
    model = Auth(**auth_json)
    with pytest.raises(DynamoDbError), mock_dynamodb() as client:
        repository = Repository(item_type=Auth, client=client)
        repository.create(item=model)
        repository.create(item=model)


def test_read_auth():
    model = Auth(**auth_json)
    with mock_dynamodb() as client:
        repository = Repository(item_type=Auth, client=client)
        repository.create(item=model)
        result = repository.read(
            KeyConditionExpression="id = :id",
            ExpressionAttributeValues={":id": model.id.dict()},
        )
    assert model == result
