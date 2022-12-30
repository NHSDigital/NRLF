import json
import time
from contextlib import contextmanager
from copy import deepcopy
from typing import Generator

import boto3
import moto
import pytest
from botocore.exceptions import ClientError

from feature_tests.common.constants import DOCUMENT_POINTER_TABLE_DEFINITION
from nrlf.core.constants import DbPrefix
from nrlf.core.errors import (
    DuplicateError,
    DynamoDbError,
    ItemNotFound,
    TooManyItemsError,
)
from nrlf.core.model import DocumentPointer, key
from nrlf.core.query import hard_delete_query, update_and_filter_query
from nrlf.core.repository import (
    MAX_TRANSACT_ITEMS,
    Repository,
    _keys,
    _validate_results_within_limits,
    handle_dynamodb_errors,
)
from nrlf.core.tests.data_factory import (
    generate_test_attachment,
    generate_test_content,
    generate_test_document_reference,
    generate_test_subject,
)
from nrlf.core.transform import (
    create_document_pointer_from_fhir_json as _create_document_pointer_from_fhir_json,
)
from nrlf.core.transform import (
    update_document_pointer_from_fhir_json as _update_document_pointer_from_fhir_json,
)
from nrlf.core.types import DynamoDbClient
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data

API_VERSION = 1
INDEX_NAME = DOCUMENT_POINTER_TABLE_DEFINITION["GlobalSecondaryIndexes"][0]["IndexName"]
create_document_pointer_from_fhir_json = (
    lambda *args, **kwargs: _create_document_pointer_from_fhir_json(
        *args, api_version=API_VERSION, **kwargs
    )
)
update_document_pointer_from_fhir_json = (
    lambda *args, **kwargs: _update_document_pointer_from_fhir_json(
        *args, api_version=API_VERSION, **kwargs
    )
)


@handle_dynamodb_errors()
def raise_exception(exception):
    raise exception


@contextmanager
def mock_dynamodb() -> Generator[DynamoDbClient, None, None]:
    with moto.mock_dynamodb():
        client: DynamoDbClient = boto3.client("dynamodb")
        client.create_table(
            TableName=DocumentPointer.kebab(), **DOCUMENT_POINTER_TABLE_DEFINITION
        )
        yield client


def test__table_name_prefix():
    repository = Repository(
        item_type=DocumentPointer, client=None, environment_prefix="foo-bar-"
    )
    assert repository.table_name == "foo-bar-document-pointer"


# ------------------------------------------------------------------------------
# Create
# ------------------------------------------------------------------------------


def test_create_document_pointer():
    fhir_json = read_test_data("nrlf")
    core_model = create_document_pointer_from_fhir_json(fhir_json=fhir_json)

    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=core_model)
        response = client.scan(TableName=DocumentPointer.kebab())

    (item,) = response["Items"]
    recovered_item = DocumentPointer(**item)

    assert recovered_item.dict() == core_model.dict()


def test_cant_create_if_item_already_exists():
    fhir_json = read_test_data("nrlf")
    core_model = create_document_pointer_from_fhir_json(fhir_json=fhir_json)
    with pytest.raises(DuplicateError), mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=core_model)
        repository.create(item=core_model)


# ------------------------------------------------------------------------------
# Read
# ------------------------------------------------------------------------------


def test_read_document_pointer():
    fhir_json = read_test_data("nrlf")
    core_model = create_document_pointer_from_fhir_json(fhir_json=fhir_json)
    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=core_model)
        result = repository.read_item(pk=core_model.pk)
    assert core_model == result


def test_read_document_pointer_throws_error_when_items_key_missing():
    fhir_json = read_test_data("nrlf")
    core_model = create_document_pointer_from_fhir_json(fhir_json=fhir_json)
    with pytest.raises(ItemNotFound), mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=core_model)
        repository.read_item(key(DbPrefix.DocumentPointer, "BAD_KEY"))


# ------------------------------------------------------------------------------
# Update
# ------------------------------------------------------------------------------


def test_update_document_pointer_success():
    old_url = "https://example.org/original_doc.pdf"
    new_url = "https://example.org/different_doc.pdf"
    doc_1 = generate_test_document_reference(
        content=generate_test_content(attachment=generate_test_attachment(url=old_url))
    )
    doc_2 = generate_test_document_reference(
        content=generate_test_content(attachment=generate_test_attachment(url=new_url))
    )

    model_1 = create_document_pointer_from_fhir_json(fhir_json=doc_1)
    time.sleep(1)  # cause times to differ
    model_2 = update_document_pointer_from_fhir_json(fhir_json=doc_2)
    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=model_1)
        repository.update(item=model_2)
        items = repository.query(model_1.pk)

    (item,) = items
    doc = json.loads(item.document.__root__)
    assert item.created_on.__root__ != model_1.created_on.__root__
    assert doc["content"][0]["attachment"]["url"] == new_url


def test_update_document_pointer_doesnt_update_if_item_doesnt_exist():
    doc_1 = generate_test_document_reference()
    model_1 = create_document_pointer_from_fhir_json(fhir_json=doc_1)
    with pytest.raises(DynamoDbError), mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.update(item=model_1)


# ------------------------------------------------------------------------------
# Supersede
# ------------------------------------------------------------------------------


def test_supersede_creates_new_item_and_deletes_existing():

    provider_id = "RJ11"
    doc_1 = generate_test_document_reference(
        provider_id=provider_id, provider_doc_id="original"
    )
    doc_2 = generate_test_document_reference(
        provider_id=provider_id, provider_doc_id="replacement"
    )

    model_1 = create_document_pointer_from_fhir_json(fhir_json=doc_1)
    model_2 = create_document_pointer_from_fhir_json(fhir_json=doc_2)

    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=model_1)
        repository.supersede(
            create_item=model_2,
            delete_pks=[model_1.pk],
        )

        repository.read_item(model_2.pk)
        try:
            repository.read_item(model_1.pk)
        except ItemNotFound as error:
            pass


def test_supersede_id_exists_raises_transaction_canceled_exception():

    fhir_json = read_test_data("nrlf")
    core_model_for_create = create_document_pointer_from_fhir_json(fhir_json=fhir_json)
    core_model_for_create.id.__root__ = (
        "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567891"
    )

    core_model_for_delete = create_document_pointer_from_fhir_json(fhir_json=fhir_json)

    with pytest.raises(Exception), mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=core_model_for_delete)
        repository.create(item=core_model_for_create)
        repository.supersede(
            create_item=core_model_for_create,
            delete_pks=[core_model_for_delete.pk],
        )


@pytest.mark.parametrize(
    "max_transact_items",
    [MAX_TRANSACT_ITEMS, MAX_TRANSACT_ITEMS + 1, MAX_TRANSACT_ITEMS * 10],
)
def test_supersede_too_many_items(max_transact_items):

    fhir_json = read_test_data("nrlf")
    core_model_for_create = create_document_pointer_from_fhir_json(fhir_json=fhir_json)
    core_model_for_create.id.__root__ = (
        "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567891"
    )
    core_model_for_delete = create_document_pointer_from_fhir_json(fhir_json=fhir_json)

    with pytest.raises(TooManyItemsError), mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.supersede(
            create_item=core_model_for_create,
            delete_pks=[core_model_for_delete.pk] * max_transact_items,
        )


def test_keys():
    actual = _keys("abc", "def", "pk_1", "sk_1")
    expected = {"pk_1": {"S": "abc"}, "sk_1": {"S": "def"}}
    assert actual == expected


# ------------------------------------------------------------------------------
# Delete
# ------------------------------------------------------------------------------


def test_hard_delete():
    doc = generate_test_document_reference()
    model = create_document_pointer_from_fhir_json(fhir_json=doc)
    with pytest.raises(ItemNotFound), mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=model)
        repository.hard_delete(model.pk)
        repository.read_item(model.pk)


def test_wont_hard_delete_if_item_doesnt_exist():
    with pytest.raises(DynamoDbError), mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.hard_delete(key(DbPrefix.DocumentPointer, "NO"))


@pytest.mark.parametrize(
    ["exception_param", "expected_exception"],
    (
        [Exception, Exception],
        [TypeError, TypeError],
        [ValueError, ValueError],
        [
            ClientError({"Error": {"Code": "ConditionalCheckFailedException"}}, "test"),
            DynamoDbError,
        ],
    ),
)
def test_wrapper_exception_handler(exception_param, expected_exception):
    with pytest.raises(expected_exception):
        raise_exception(exception_param)


# ------------------------------------------------------------------------------
# Search
# ------------------------------------------------------------------------------


def test_search_returns_multiple_values_with_same_nhs_number():
    doc_1 = generate_test_document_reference(provider_doc_id="1234")
    doc_2 = generate_test_document_reference(provider_doc_id="2345")

    model_1 = create_document_pointer_from_fhir_json(fhir_json=doc_1)
    model_2 = create_document_pointer_from_fhir_json(fhir_json=doc_2)

    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=model_1)
        repository.create(item=model_2)
        items = repository.query_gsi_1(model_1.pk_1)
    assert len(items) == 2


def test_search_returns_correct_values():
    doc_1 = generate_test_document_reference(
        provider_doc_id="FIRST", subject=generate_test_subject("9278693472")
    )
    doc_2 = generate_test_document_reference(
        provider_doc_id="SECOND", subject=generate_test_subject("3137554160")
    )
    model_1 = create_document_pointer_from_fhir_json(fhir_json=doc_1)
    model_2 = create_document_pointer_from_fhir_json(fhir_json=doc_2)
    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=model_1)
        repository.create(item=model_2)

        docs_gsi_1 = repository.query_gsi_1(model_1.pk_1)  # NHS Number / Subject
        docs_gsi_2 = repository.query_gsi_2(model_1.pk_2)  # ODS Code / Custodian

    assert len(docs_gsi_1) == 1, "Partitioned by subject"
    assert len(docs_gsi_2) == 2, "Partitioned by provider"


# ------------------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------------------


def test_validate_results_less_than_100_items():
    array_size = 99
    items = [""] * array_size
    request_results = {"Items": items, "Count": array_size, "ScannedCount": array_size}
    result = _validate_results_within_limits(request_results)
    assert result == request_results


def test_validate_results_throws_exception_when_more_than_100_items():
    array_size = 101
    items = [""] * array_size
    request_results = {"Items": items, "Count": array_size, "ScannedCount": array_size}

    with pytest.raises(Exception) as error:
        _validate_results_within_limits(request_results)
        assert (
            error.value
            == "DynamoDB has returned too many results, pagination not implemented yet"
        )


def test_validate_results_throws_exception_when_last_evaluated_key_exists():
    array_size = 98
    items = [""] * array_size
    request_results = {
        "Items": items,
        "Count": array_size,
        "ScannedCount": array_size,
        "LastEvaluatedKey": array_size,
    }

    with pytest.raises(Exception) as error:
        _validate_results_within_limits(request_results)
        assert (
            error.value
            == "DynamoDB has returned too many results, pagination not implemented yet"
        )
