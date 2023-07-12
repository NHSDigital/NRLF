import pytest

from nrlf.core.constants import DbPrefix
from nrlf.core.errors import ItemNotFound
from nrlf.core.model import DocumentPointer, key
from nrlf.core.query import (
    create_filter_query,
    create_updated_expression_query,
    to_dynamodb_dict,
)
from nrlf.core.repository import Repository
from nrlf.core.tests.data_factory import (
    SNOMED_CODES_END_OF_LIFE_CARE_COORDINATION_SUMMARY,
    SNOMED_CODES_MENTAL_HEALTH_CRISIS_PLAN,
    generate_test_custodian,
    generate_test_document_reference,
    generate_test_document_type,
    generate_test_nhs_number,
    generate_test_subject,
)
from nrlf.core.tests.test_document_pointers_repository import mock_dynamodb
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
    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=core_model)
        item = repository.read_item(core_model.pk.__root__)
        assert item == core_model


def test_filter_query_in_db_not_found():
    with pytest.raises(ItemNotFound), mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.read_item(key(DbPrefix.DocumentPointer, "NOT_FOUND"))


def test_create_search_and_filter_query_in_db():
    nhs_number = generate_test_nhs_number()
    snomed_code = "736253002"
    doc = generate_test_document_reference(
        subject=generate_test_subject(nhs_number),
        type=generate_test_document_type(snomed_code),
    )
    model = create_document_pointer_from_fhir_json(doc, 99)

    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=model)
        result = repository.query_gsi_1(
            model.pk_1.__root__, type="http://snomed.info/sct|736253002"
        )
        assert result.items == [model]


def test_query_can_filter_results():
    provider_id = "RX1"
    nhs_number = generate_test_nhs_number()
    doc_1 = generate_test_document_reference(
        provider_id=provider_id,
        provider_doc_id="OK",
        type=generate_test_document_type(SNOMED_CODES_MENTAL_HEALTH_CRISIS_PLAN),
        subject=generate_test_subject(nhs_number),
        custodian=generate_test_custodian(provider_id),
    )
    doc_2 = generate_test_document_reference(
        provider_id=provider_id,
        provider_doc_id="Missing",
        type=generate_test_document_type(
            SNOMED_CODES_END_OF_LIFE_CARE_COORDINATION_SUMMARY
        ),
        subject=generate_test_subject(nhs_number),
        custodian=generate_test_custodian(provider_id),
    )
    model_1 = create_document_pointer_from_fhir_json(doc_1, 99)
    model_2 = create_document_pointer_from_fhir_json(doc_2, 99)

    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=model_1)
        repository.create(item=model_2)
        results_1 = repository.query_gsi_1(
            pk=key(DbPrefix.Patient, nhs_number),
            type=[f"http://snomed.info/sct|{SNOMED_CODES_MENTAL_HEALTH_CRISIS_PLAN}"],
        )
        results_2 = repository.query_gsi_2(
            pk=key(DbPrefix.Organization, provider_id),
            type=[f"http://snomed.info/sct|{SNOMED_CODES_MENTAL_HEALTH_CRISIS_PLAN}"],
        )
        assert len(results_1.items) == 1
        assert results_1.items[0] == model_1
        assert len(results_2.items) == 1
        assert results_2.items[0] == model_1


def test_filter_can_find_result():
    snomed_code = "736253002"
    doc = generate_test_document_reference(
        type=generate_test_document_type(snomed_code)
    )
    model = create_document_pointer_from_fhir_json(doc, 99)

    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=model)
        item = repository.read_item(
            pk=model.pk.__root__, type=["http://snomed.info/sct|736253002"]
        )
        assert item == model


def test_filter_cannot_find_result():
    snomed_code = "736253002"
    doc = generate_test_document_reference(
        type=generate_test_document_type(snomed_code)
    )
    model = create_document_pointer_from_fhir_json(doc, 99)

    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        repository.create(item=model)
        with pytest.raises(ItemNotFound):
            repository.read_item(
                pk=model.pk.__root__, type=["http://snomed.info/sct|WRONG"]
            )


def test_create_search_and_filter_query_in_db_returns_empty_bundle():
    with mock_dynamodb() as client:
        repository = Repository(item_type=DocumentPointer, client=client)
        item = repository.query_gsi_1(
            pk=key(DbPrefix.Patient, "EMPTY"),
            type=["http://snomed.info/sct|736253002"],
        )
        assert len(item.items) == 0


@pytest.mark.parametrize(
    ("values", "expected"),
    (
        (
            {
                "foo": {"N": "123"},
                "bar": {"S": "456"},
                "created_on": {"S": "test"},
                "producer_id": {"S": "TEST PRODUCER"},
            },
            {
                "ConditionExpression": "attribute_exists(id) AND #producer_id = :producer_id",
                "UpdateExpression": "SET #foo=:foo,#bar=:bar,#producer_id=:producer_id",
                "ExpressionAttributeValues": {
                    ":foo": {"N": "123"},
                    ":bar": {"S": "456"},
                    ":producer_id": {"S": "TEST PRODUCER"},
                },
                "ExpressionAttributeNames": {
                    "#foo": "foo",
                    "#bar": "bar",
                    "#producer_id": "producer_id",
                },
            },
        ),
    ),
)
def test_create_updated_expression_query(values, expected):
    assert create_updated_expression_query(**values) == expected
