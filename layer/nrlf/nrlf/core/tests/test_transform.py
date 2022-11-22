import pytest
from nrlf.core.errors import FhirValidationError
from nrlf.core.model import DocumentPointer
from nrlf.core.transform import (
    create_bundle_entries_from_document_pointers,
    create_document_pointer_from_fhir_json,
    pagination_parameters,
    validate_no_extra_fields,
)
from nrlf.producer.fhir.r4.model import BundleEntry, DocumentReference
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data
from pydantic import BaseModel


class Foo(BaseModel):
    spam: str
    eggs: int


def test_validate_no_extra_fields_success():
    json_without_extra_fields = {"spam": "SPAM", "eggs": 123}
    json_as_model = Foo(**json_without_extra_fields)
    validate_no_extra_fields(
        json_as_model.dict(exclude_none=True), json_without_extra_fields
    )


def test_validate_no_extra_fields_failure():
    json_with_extra_fields = {"spam": "SPAM", "eggs": 123, "bar": "BAR"}
    json_as_model = Foo(**json_with_extra_fields)
    with pytest.raises(FhirValidationError):
        validate_no_extra_fields(
            json_as_model.dict(exclude_none=True), json_with_extra_fields
        )


def test_create_document_references_from_document_pointers():
    fhir_json = read_test_data("nrlf")
    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=1
    )

    document_reference = DocumentReference(**fhir_json)
    expected_reference = [BundleEntry(resource=document_reference)]

    result = create_bundle_entries_from_document_pointers([core_model])

    assert result == expected_reference


def test_create_document_references_from_document_pointers_multiple():
    fhir_json = read_test_data("nrlf")
    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=1
    )
    core_model_2 = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=1
    )

    document_reference = DocumentReference(**fhir_json)
    expected_reference = [
        BundleEntry(resource=document_reference),
        BundleEntry(resource=document_reference),
    ]

    result = create_bundle_entries_from_document_pointers([core_model, core_model_2])

    assert result == expected_reference


@pytest.mark.parametrize(
    ("queries", "expected"),
    (
        (
            {"subject": "foo", "page": "1", "asc": "true", "pagesize": "3"},
            {"pagesize": 3, "page": 1, "order": "true"},
        ),
        (
            {"subject": "foo"},
            {"pagesize": 20, "page": 0, "order": "false"},
        ),
        (
            {"subject": "foo", "pagesize": "101", "asc": "foo"},
            {"pagesize": 100, "page": 0, "order": "foo"},
        ),
    ),
)
def test_sort_parameters(queries, expected):
    params = pagination_parameters(**queries)
    assert params == expected
