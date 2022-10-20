from contextlib import contextmanager
from http import client
from unittest.mock import mock_open
from nrlf.core.validators import make_timestamp
import moto
import json
from datetime import datetime as dt
from nrlf.core.model import DocumentPointer, create_document_pointer_from_fhir_json
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data
import pytest
from nrlf.core.repository import Repository
import boto3
from datetime import datetime

DEFAULT_ATTRIBUTE_DEFINITIONS = [{"AttributeName": "id", "AttributeType": "S"}]
DEFAULT_KEY_SCHEMA = [{"AttributeName": "id", "KeyType": "HASH"}]


@contextmanager
def mock_dynamodb(table_name):
    with moto.mock_dynamodb():
        client = boto3.client("dynamodb")
        client.create_table(
            AttributeDefinitions=DEFAULT_ATTRIBUTE_DEFINITIONS,
            TableName=table_name,
            KeySchema=DEFAULT_KEY_SCHEMA,
            BillingMode="PAY_PER_REQUEST",
        )
        yield client


def test_create_document_pointer():
    # Arrange
    document_reference = json.dumps(read_test_data("nrlf"))
    api_version = 1
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )
    table_name = "document-pointer"

    with mock_dynamodb(table_name) as client:
        repository = Repository(table_name)

        # Act
        repository.create(item=core_model.dict())
        response = client.scan(TableName=table_name)

    (item,) = response["Items"]
    recovered_item = DocumentPointer.construct(**item)

    # Assert
    assert recovered_item.dict() == core_model.dict()


def test_read_document_pointer():
    # Arrange
    document_reference = json.dumps(read_test_data("nrlf"))
    api_version = 1
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )
    table_name = "document-pointer"

    with mock_dynamodb(table_name) as client:
        repository = Repository(table_name)
        repository.create(item=core_model.dict())

        # Act
        result = repository.read(core_model.id.value)

    # Assert
    assert core_model == result["Item"]


def test_update_document_pointer():
    # Arrange
    document_reference = json.dumps(read_test_data("nrlf"))

    updated_document = read_test_data("nrlf")
    updated_document["content"][0]["attachment"][
        "url"
    ] = "https://example.org/different_doc.pdf"

    updated_document_reference = json.dumps(updated_document)

    api_version = 1

    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )
    updated_core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=updated_document_reference, api_version=api_version
    )
    table_name = "document-pointer"

    with mock_dynamodb(table_name) as client:
        repository = Repository(table_name)
        repository.create(item=core_model.dict())

        # Act
        repository.update(item=updated_core_model.dict())
        response = client.scan(TableName=table_name)

    (item,) = response["Items"]
    recovered_item = DocumentPointer.construct(**item)

    # Assert
    assert recovered_item.dict() == updated_core_model.dict()


def test_soft_delete():
    # Arrange
    document_reference = json.dumps(read_test_data("nrlf"))

    api_version = 1
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )
    table_name = "document-pointer"

    with mock_dynamodb(table_name) as client:
        repository = Repository(table_name)
        repository.create(item=core_model.dict())

        # Act
        repository.soft_delete(core_model.id.value)
        response = client.scan(TableName=table_name)

    (item,) = response["Items"]

    recovered_item = DocumentPointer.construct(**item)
    now = datetime.now().date()
    deleted_date = datetime.strptime(
        recovered_item.deleted_on["S"], "%Y-%m-%dT%H:%M:%S.%fZ"
    ).date()

    # Assert
    assert now == deleted_date


def test_hard_delete():
    # Arrange
    document_reference = json.dumps(read_test_data("nrlf"))

    api_version = 1
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )
    table_name = "document-pointer"

    with mock_dynamodb(table_name) as client:
        repository = Repository(table_name)
        repository.create(item=core_model.dict())

        # Act
        repository.hard_delete(core_model.id.value)
        response = client.scan(TableName=table_name)

    print(response)
    # Assert
    assert len(response["Items"]) == 0


def test_search():
    pass
