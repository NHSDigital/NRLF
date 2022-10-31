import pytest
from nrlf.core.errors import ItemNotFound
from nrlf.core.model import DocumentPointer
from nrlf.core.query import (
    create_filter_query,
    create_read_and_filter_query,
    to_dynamodb_dict,
)
from nrlf.core.repository import Repository
from nrlf.core.tests.test_repository import mock_dynamodb
from nrlf.core.transform import create_document_pointer_from_fhir_json
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data


@pytest.mark.parametrize(
    ("value", "expected"),
    (("foo", {"S": "foo"}), (123, {"N": "123"}), (None, {"NULL": True})),
)
def test__to_dynamodb_dict(value, expected):
    assert to_dynamodb_dict(value) == expected


@pytest.mark.parametrize(
    ("filters", "expected"),
    (
        (
            {"foo": 123, "bar": "456"},
            {
                "FilterExpression": "#foo = :foo AND #bar = :bar",
                "ExpressionAttributeValues": {
                    ":foo": {"N": "123"},
                    ":bar": {"S": "456"},
                },
                "ExpressionAttributeNames": {"#foo": "foo", "#bar": "bar"},
            },
        ),
        (
            {"foo": [123, 456], "bar": "456"},
            {
                "FilterExpression": "#foo IN (:foo0,:foo1) AND #bar = :bar",
                "ExpressionAttributeValues": {
                    ":foo0": {"N": "123"},
                    ":foo1": {"N": "456"},
                    ":bar": {"S": "456"},
                },
                "ExpressionAttributeNames": {"#foo": "foo", "#bar": "bar"},
            },
        ),
    ),
)
def test_create_filter_query(filters, expected):
    assert create_filter_query(**filters) == expected


def test_filter_query_in_db():
    fhir_json = read_test_data("nrlf")
    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=1
    )
    query = create_filter_query(type="https://snomed.info/ict|736253002")
    query["ExpressionAttributeValues"][":id"] = core_model.id.dict()

    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=core_model)
        item = repository.read(KeyConditionExpression="id = :id", **query)
        assert item == core_model


def test_filter_query_in_db_not_found():
    fhir_json = read_test_data("nrlf")
    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=1
    )
    query = create_filter_query(type="123")
    query["ExpressionAttributeValues"][":id"] = core_model.id.dict()

    with pytest.raises(ItemNotFound), mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=core_model)
        repository.read(KeyConditionExpression="id = :id", **query)


def test_create_read_and_filter_query_in_db():
    fhir_json = read_test_data("nrlf")
    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=1
    )
    query = create_read_and_filter_query(
        id=core_model.id.__root__, type="https://snomed.info/ict|736253002"
    )

    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=core_model)
        item = repository.read(**query)
        assert item == core_model
