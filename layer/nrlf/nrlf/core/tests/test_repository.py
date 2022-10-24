import json
from contextlib import contextmanager
from http import client

import boto3
import moto
import pytest
from nrlf.core.dynamodb_types import DynamoDbType
from nrlf.core.errors import DynamoDbError, ItemNotFound
from nrlf.core.model import DocumentPointer
from nrlf.core.repository import Repository, _to_kebab_case, handle_dynamodb_errors
from nrlf.core.transform import create_document_pointer_from_fhir_json
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data
from pydantic import BaseModel

DEFAULT_ATTRIBUTE_DEFINITIONS = [{"AttributeName": "id", "AttributeType": "S"}]
DEFAULT_KEY_SCHEMA = [{"AttributeName": "id", "KeyType": "HASH"}]
TABLE_NAME = _to_kebab_case(DocumentPointer.__name__)


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
    class TestClass(BaseModel):
        field: str

    with pytest.raises(TypeError) as error, mock_dynamodb(TABLE_NAME) as client:
        Repository(TestClass, client)

    (message,) = error.value.args
    assert message == "Model contains fields that are not of type DynamoDbType"


def test_fields_are_all_dynamo_db_type():
    with mock_dynamodb(TABLE_NAME):
        Repository(DocumentPointer, client)


def test_create_document_pointer():

    document_reference = json.dumps(read_test_data("nrlf"))
    api_version = 1
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )

    with mock_dynamodb(TABLE_NAME) as client:
        repository = Repository(DocumentPointer, client)

        repository.create(item=core_model)
        response = client.scan(TableName=TABLE_NAME)

    (item,) = response["Items"]
    recovered_item = DocumentPointer.construct(**item)

    assert recovered_item.dict() == core_model.dict()


def test_cant_create_if_item_already_exists():

    document_reference = json.dumps(read_test_data("nrlf"))
    api_version = 1
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )

    with pytest.raises(DynamoDbError) as error, mock_dynamodb(TABLE_NAME) as client:
        repository = Repository(DocumentPointer, client)

        repository.create(item=core_model)
        repository.create(item=core_model)


def test_read_document_pointer():

    document_reference = json.dumps(read_test_data("nrlf"))
    api_version = 1
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )

    with mock_dynamodb(TABLE_NAME) as client:
        repository = Repository(DocumentPointer, client)
        repository.create(item=core_model)

        result = repository.read(id=core_model.id.value)

    assert core_model == result


def test_read_document_pointer_throws_error_when_items_key_missing():

    document_reference = json.dumps(read_test_data("nrlf"))
    api_version = 1
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )

    with pytest.raises(ItemNotFound) as error, mock_dynamodb(TABLE_NAME) as client:
        repository = Repository(DocumentPointer, client)
        repository.create(item=core_model)

        repository.read(id={"S": "badKey"})


def test_update_document_pointer():

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

    with mock_dynamodb(TABLE_NAME) as client:
        repository = Repository(DocumentPointer, client)
        repository.create(item=core_model)

        repository.update(item=updated_core_model)
        response = client.scan(TableName=TABLE_NAME)

    (item,) = response["Items"]
    recovered_item = DocumentPointer.construct(**item)

    assert recovered_item.dict() == updated_core_model.dict()


def test_update_document_pointer_doesnt_update_if_item_doesnt_exist():

    updated_document = read_test_data("nrlf")
    updated_document["content"][0]["attachment"][
        "url"
    ] = "https://example.org/different_doc.pdf"

    updated_document_reference = json.dumps(updated_document)

    api_version = 1

    updated_core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=updated_document_reference, api_version=api_version
    )

    with pytest.raises(DynamoDbError):
        repository = Repository(DocumentPointer, client)

        repository.update(item=updated_core_model.dict())


def test_supersede_creates_new_item_and_deletes_existing():

    document_reference = json.dumps(read_test_data("nrlf"))
    api_version = 1
    core_model_for_create = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )

    core_model_for_create.id = DynamoDbType[str](
        value="ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567891"
    )

    core_model_for_delete = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )

    with mock_dynamodb(TABLE_NAME) as client:
        repository = Repository(DocumentPointer, client)
        repository.create(item=core_model_for_delete)

        repository.supersede(
            create_item=core_model_for_create,
            delete_item_id=core_model_for_delete.id.value,
        )

        response_for_created_item = repository.read(id=core_model_for_create.id.value)

        try:
            repository.read(id=core_model_for_delete.id.value)
        except ItemNotFound as error:
            assert error.args[0] == "Item could not be found"

    assert response_for_created_item == core_model_for_create


def test_supersede_id_exists_raises_transaction_canceled_exception():

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

    with pytest.raises(Exception) as error, mock_dynamodb(TABLE_NAME) as client:
        repository = Repository(DocumentPointer, client)
        repository.create(item=core_model_for_delete)
        repository.create(item=core_model_for_create)

        repository.supersede(
            create_item=core_model_for_create.dict(),
            delete_item_id=core_model_for_delete.id.value,
        )


def test_hard_delete():

    document_reference = json.dumps(read_test_data("nrlf"))

    api_version = 1
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document_reference, api_version=api_version
    )

    with mock_dynamodb(TABLE_NAME) as client:
        repository = Repository(DocumentPointer, client)
        repository.create(item=core_model)

        repository.hard_delete(core_model.id.value)
        response = client.scan(TableName=TABLE_NAME)

    assert len(response["Items"]) == 0


def test_wont_hard_delete_if_item_doesnt_exist():

    with pytest.raises(DynamoDbError), mock_dynamodb(TABLE_NAME) as client:
        repository = Repository(DocumentPointer, client)

        repository.hard_delete(id="no")


@handle_dynamodb_errors
def raise_exception(exception):
    raise exception


@pytest.mark.parametrize(
    ["exception_param"],
    ([Exception], [TypeError], [ValueError]),
)
def test_wrapper_exception_handler(exception_param):

    with pytest.raises(DynamoDbError):
        raise_exception(exception_param)


def test_search():
    pass
