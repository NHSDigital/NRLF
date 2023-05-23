import time
from contextlib import contextmanager
from itertools import chain
from math import ceil
from typing import Generator

import boto3
import moto
import pytest
from botocore.exceptions import ClientError

from feature_tests.common.constants import DOCUMENT_POINTER_TABLE_DEFINITION
from feature_tests.common.repository import FeatureTestRepository
from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json
from nrlf.core.constants import ODS_SYSTEM, DbPrefix
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
from nrlf.core.validators import json_loads
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

SUBJECT = "9278693472"


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
        result = repository.read_item(pk=core_model.pk.__root__)
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
        item = repository.read_item(model_1.pk.__root__)

    doc = json_loads(item.document.__root__)
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

        repository.read_item(model_2.pk.__root__)
        try:
            repository.read_item(model_1.pk.__root__)
        except ItemNotFound:
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
        repository.hard_delete(model.pk.__root__)
        repository.read_item(model.pk.__root__)


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
        item = repository.query_gsi_1(model_1.pk_1.__root__)

    assert len(item.document_pointers) == 2


def test_search_returns_correct_values():
    doc_1 = generate_test_document_reference(
        provider_doc_id="FIRST", subject=generate_test_subject(SUBJECT)
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
            model_1.pk_1.__root__
        )  # NHS Number / Subject
        docs_gsi_2_response = repository.query_gsi_2(
            model_1.pk_2.__root__
        )  # ODS Code / Custodian

    assert len(docs_gsi_1_response.document_pointers) == 1, "Partitioned by subject"
    assert len(docs_gsi_2_response.document_pointers) == 2, "Partitioned by provider"


def _create_items(
    doc_ids: list[str], repository: Repository, subject: str, custodian: str
) -> list[DocumentPointer]:
    items: list[DocumentPointer] = []
    for doc_id in doc_ids:
        doc = generate_test_document_reference(
            provider_doc_id=doc_id,
            subject=generate_test_subject(subject),
            custodian={"identifier": {"value": custodian, "system": ODS_SYSTEM}},
        )
        item = create_document_pointer_from_fhir_json(fhir_json=doc)
        repository.create(item=item)
        items.append(item)

    return items


def _document_pointer_collection_are_same(
    a: list[DocumentPointer], b: list[DocumentPointer]
):
    return sorted(a, key=lambda doc: doc.pk.__root__) == sorted(
        b, key=lambda doc: doc.pk.__root__
    )


def _create_items_in_alternate_batches(
    a_batch_sizes: list[int],
    b_batch_sizes: list[int],
    repository,
    a_custodian,
    b_custodian,
):
    a_batch_sizes = a_batch_sizes.copy()  # destructive operation below, so need to copy
    b_batch_sizes = b_batch_sizes.copy()
    a_docs, b_docs = [], []
    while a_batch_sizes or b_batch_sizes:
        if a_batch_sizes:
            start, end = len(a_docs), len(a_docs) + a_batch_sizes.pop(-1)
            a_docs += _create_items(
                doc_ids=list(map(str, range(start, end))),
                repository=repository,
                subject=SUBJECT,
                custodian=a_custodian,
            )
        if b_batch_sizes:
            start, end = len(b_docs), len(b_docs) + b_batch_sizes.pop(-1)
            b_docs += _create_items(
                doc_ids=list(map(str, range(start, end))),
                repository=repository,
                subject=SUBJECT,
                custodian=b_custodian,
            )
    return a_docs, b_docs


BATCH_SIZES = (
    [],
    [0, PAGE_ITEM_LIMIT + 3, 4, 3 * PAGE_ITEM_LIMIT],
    [PAGE_ITEM_LIMIT - 2, 0, 0, PAGE_ITEM_LIMIT + 3, 3],
)


@pytest.mark.integration
@pytest.mark.parametrize("foo_batch_sizes", BATCH_SIZES)
@pytest.mark.parametrize("bar_batch_sizes", BATCH_SIZES)
def test_scroll_gsi_1(bar_batch_sizes, foo_batch_sizes, dynamodb_client):
    """
    Explanation:
        * dynamodb applies filters results post-query *per page*, so it is possible for the following scenario:
            * a given PK (e.g. subject always equals "123")
            * multiple possible values of a filter (e.g. custodian="foo" or "bar")
            * a globally unique sort key which is independent of the filter (e.g. a created date)
         that the following effect can be observed when supplying a filter:
            a) get fewer results than PAGE_SIZE *per page* from a single query that should in total
               yield at least PAGE_SIZE results
            b) have more pages of results even if the current page is empty
            c) have more pages of results where some or all of those pages are empty
        * the above scenario applies to at least GSI One
    """

    total_expected_docs = sum(foo_batch_sizes)
    # NB: zero docs still means one page, hence 'or 1'
    n_expected_pages = ceil(total_expected_docs / PAGE_ITEM_LIMIT) or 1
    total_other_docs = sum(bar_batch_sizes)

    repository = FeatureTestRepository(
        item_type=DocumentPointer,
        client=dynamodb_client,
        environment_prefix=f'{get_terraform_json()["prefix"]["value"]}--',
    )

    # Create docs in alternate batches (since created data will therefore alternate)
    # and validate that we've created what we expect
    foo_docs, bar_docs = _create_items_in_alternate_batches(
        a_batch_sizes=foo_batch_sizes,
        a_custodian="foo",
        b_batch_sizes=bar_batch_sizes,
        b_custodian="bar",
        repository=repository,
    )
    assert total_expected_docs == len(foo_docs)
    assert total_other_docs == len(bar_docs)

    # Scroll to get all results by GSI One for filter "foo"
    pages = []
    last_evaluated_key = None
    last_evaluated_keys = []
    for _ in range(n_expected_pages + 10):  # allow to scroll 10 more than anticipated
        response = repository.query_gsi_1(
            pk=f"P#{SUBJECT}", producer_id="foo", exclusive_start_key=last_evaluated_key
        )
        last_evaluated_key = response.last_evaluated_key

        pages.append(response.document_pointers)
        if not last_evaluated_key:
            break
        else:
            last_evaluated_keys.append(last_evaluated_key)

    # Test that all pages have size PAGE_ITEM_LIMIT, except the final page
    assert len(pages) == n_expected_pages
    if len(pages) > 1:
        assert all(len(page) == PAGE_ITEM_LIMIT for page in pages[:-1])
    if len(pages) > 0:
        assert len(last_evaluated_keys) == len(pages) - 1
        assert len(pages[-1]) <= PAGE_ITEM_LIMIT

    # Test that we have retrieved all the expected documents
    retrieved_items = list(chain.from_iterable(pages))  # Flatten list of lists
    n_unique_items = len(set(item.pk.__root__ for item in retrieved_items))  # dupes
    assert n_unique_items == len(retrieved_items) == total_expected_docs
    assert _document_pointer_collection_are_same(a=retrieved_items, b=foo_docs)
    assert last_evaluated_key is None
