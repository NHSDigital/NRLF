import json
from contextlib import contextmanager
from datetime import datetime
from http import client
from unittest.mock import mock_open

import boto3
import moto
import pytest
from nrlf.core.model import DocumentPointer, create_document_pointer_from_fhir_json
from nrlf.core.repository import Repository
from nrlf.core.validators import make_timestamp
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data
from pydantic import BaseModel

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


def test_fields_are_not_all_dynamo_db_type():
    # Arrange
    class TestClass(BaseModel):
        field: str

    table_name = "document-pointer"

    with pytest.raises(TypeError) as error, mock_dynamodb(table_name) as client:
        repository = Repository(TestClass, client)

    # Assert
    (message,) = error.value.args
    assert message == "Model contains fields that are not of type DynamoDbType"


def test_fields_are_all_dynamo_db_type():
    # Arrange
    table_name = "document-pointer"

    with mock_dynamodb(table_name):
        Repository(DocumentPointer, client)


def test_create_document_pointer():
    # Arrange
    document_reference = json.dumps(read_test_data("nrlf"))
    api_version = 1
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )
    table_name = "document-pointer"

    with mock_dynamodb(table_name) as client:
        repository = Repository(DocumentPointer, client)

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
        repository = Repository(DocumentPointer, client)
        repository.create(item=core_model.dict())

        # Act
        result = repository.read(id=core_model.id.value)

    # Assert
    assert core_model == result


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
        repository = Repository(DocumentPointer, client)
        repository.create(item=core_model.dict())

        # Act
        repository.update(item=updated_core_model.dict())
        response = client.scan(TableName=table_name)

    (item,) = response["Items"]
    recovered_item = DocumentPointer.construct(**item)

    # Assert
    assert recovered_item.dict() == updated_core_model.dict()


def test_supersede():
    # Arrange
    document_reference = json.dumps(read_test_data("nrlf"))
    api_version = 1
    core_model_for_create = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )
    core_model_for_create.id.value = {
        "S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567891"
    }

    core_model_for_delete = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )

    table_name = "document-pointer"

    with mock_dynamodb(table_name) as client:
        repository = Repository(DocumentPointer, client)
        repository.create(item=core_model_for_delete.dict())

        # Act
        repository.supersede(
            create_item=core_model_for_create.dict(),
            delete_item_id=core_model_for_delete.id.value,
        )
        response = client.scan(TableName=table_name)

    (item,) = response["Items"]
    recovered_item = DocumentPointer.construct(**item)

    # Assert
    assert recovered_item.dict() == core_model_for_create.dict()


def test_soft_delete():
    # Arrange
    document_reference = json.dumps(read_test_data("nrlf"))

    api_version = 1
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )
    table_name = "document-pointer"

    with mock_dynamodb(table_name) as client:
        repository = Repository(DocumentPointer, client)
        repository.create(item=core_model.dict())

        # Act
        repository.soft_delete_document_pointer(core_model.id.value)
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
        repository = Repository(DocumentPointer, client)
        repository.create(item=core_model.dict())

        # Act
        repository.hard_delete(core_model.id.value)
        response = client.scan(TableName=table_name)

    # Assert
    assert len(response["Items"]) == 0


def test_search():
    pass
