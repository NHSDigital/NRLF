import json
import time
from contextlib import contextmanager
from typing import Generator

import boto3
import moto
import pytest
from botocore.exceptions import ClientError
from nrlf.core.constants import DbPrefix
from nrlf.core.errors import (
    DuplicateError,
    DynamoDbError,
    ItemNotFound,
    TooManyItemsError,
)
from nrlf.core.model import DocumentPointer, key
from nrlf.core.repository import (
    MAX_TRANSACT_ITEMS,
    PAGE_ITEM_LIMIT,
    Repository,
    _keys,
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

from feature_tests.common.constants import DOCUMENT_POINTER_TABLE_DEFINITION
from feature_tests.common.repository import FeatureTestRepository
from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json

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


@pytest.fixture(scope="session")
def dynamodb_client():
    session = new_aws_session()
    return session.client("dynamodb")


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
        item = repository.read_item(model_1.pk)

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
        item = repository.query_gsi_1(model_1.pk_1)

    assert len(item.document_pointers) == 2


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

        docs_gsi_1_response = repository.query_gsi_1(
            model_1.pk_1
        )  # NHS Number / Subject
        docs_gsi_2_response = repository.query_gsi_2(
            model_1.pk_2
        )  # ODS Code / Custodian

    assert len(docs_gsi_1_response.document_pointers) == 1, "Partitioned by subject"
    assert len(docs_gsi_2_response.document_pointers) == 2, "Partitioned by provider"


def test_query_last_evaluated_key_is_returned_in_correct_circumstance():
    doc_1 = generate_test_document_reference(
        provider_doc_id="FIRST", subject=generate_test_subject("9278693472")
    )
    doc_2 = generate_test_document_reference(
        provider_doc_id="SECOND", subject=generate_test_subject("9278693472")
    )
    model_1 = create_document_pointer_from_fhir_json(fhir_json=doc_1)
    model_2 = create_document_pointer_from_fhir_json(fhir_json=doc_2)
    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=model_1)
        repository.create(item=model_2)

        response = repository.query_gsi_1(model_1.pk_1, limit=1)  # NHS Number / Subject
        response2 = repository.query_gsi_1(
            model_1.pk_1, limit=2
        )  # NHS Number / Subject

    assert response.last_evaluated_key is not None
    assert response2.last_evaluated_key is None


def _create_items_to_scroll(n_pages_of_docs, repository) -> list[DocumentPointer]:
    items: list[DocumentPointer] = []
    for i in range(PAGE_ITEM_LIMIT * n_pages_of_docs):
        doc = generate_test_document_reference(
            provider_doc_id=f"id{i}", subject=generate_test_subject("9278693472")
        )
        item = create_document_pointer_from_fhir_json(fhir_json=doc)
        repository.create(item=item)
        items.append(item)

    return items


def _query_all_pages(n_pages_of_docs, repository, pk) -> list[DocumentPointer]:
    retrieved_items = []

    # Scroll first n-1 pages
    last_evaluated_key = None
    for _ in range(n_pages_of_docs - 1):
        response = repository.query_gsi_1(pk, exclusive_start_key=last_evaluated_key)
        last_evaluated_key = response.last_evaluated_key
        assert len(response.document_pointers) == PAGE_ITEM_LIMIT
        assert last_evaluated_key is not None
        retrieved_items += response.document_pointers

    # Scroll final page
    response = repository.query_gsi_1(pk, exclusive_start_key=last_evaluated_key)
    assert len(response.document_pointers) == PAGE_ITEM_LIMIT
    assert (
        response.last_evaluated_key is None
    )  # Note: this is now None, since the last page
    retrieved_items += response.document_pointers
    return retrieved_items


def document_pointer_collection_are_same(
    a: list[DocumentPointer], b: list[DocumentPointer]
):
    assert len(a) == len(b)
    assert all(item in a for item in b)
    assert all(item in b for item in a)


def _test_query_last_evaluated_key_is_not_returned_at_page_limit(
    repository_type, client, n_pages_of_docs, environment_prefix=""
):
    repository = repository_type(
        item_type=DocumentPointer, client=client, environment_prefix=environment_prefix
    )
    items = _create_items_to_scroll(n_pages_of_docs, repository)
    retrieved_items = _query_all_pages(n_pages_of_docs, repository, items[0].pk_1)
    document_pointer_collection_are_same(a=items, b=retrieved_items)


@pytest.mark.parametrize("n_pages_of_docs", range(1, 5))
def test_query_last_evaluated_key_is_not_returned_at_page_limit(n_pages_of_docs):
    with mock_dynamodb() as client:
        _test_query_last_evaluated_key_is_not_returned_at_page_limit(
            repository_type=Repository, client=client, n_pages_of_docs=n_pages_of_docs
        )


@pytest.mark.integration
@pytest.mark.parametrize("n_pages_of_docs", range(1, 5))
def test_query_last_evaluated_key_is_not_returned_at_page_limit_integration(
    n_pages_of_docs, dynamodb_client
):
    environment_prefix = f'{get_terraform_json()["prefix"]["value"]}--'
    _test_query_last_evaluated_key_is_not_returned_at_page_limit(
        repository_type=FeatureTestRepository,
        client=dynamodb_client,
        n_pages_of_docs=n_pages_of_docs,
        environment_prefix=environment_prefix,
    )
