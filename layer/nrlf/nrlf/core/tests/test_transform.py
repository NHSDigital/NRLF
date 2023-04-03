import pytest
from nrlf.core.errors import FhirValidationError, NextPageTokenValidationError
from nrlf.core.transform import (
    _strip_empty_json_paths,
    create_bundle_entries_from_document_pointers,
    create_document_pointer_from_fhir_json,
    transform_next_page_token_to_start_key,
    validate_no_extra_fields,
)
from nrlf.producer.fhir.r4.model import BundleEntry, DocumentReference
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data
from pydantic import BaseModel


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            {"foo": "bar", "baz": [{"spam": None, "eggs": ""}, {"bam": "wap"}]},
            {"foo": "bar", "baz": [{"bam": "wap"}]},
        ),
        (
            {"foo": None, "baz": [{"spam": "eggs"}, {"bam": ""}]},
            {"baz": [{"spam": "eggs"}]},
        ),
        (
            {"foo": {"spam": None}},
            None,
        ),
    ],
)
def test__strip_empty_json_paths(input, expected):
    assert _strip_empty_json_paths(input) == expected


@pytest.mark.parametrize(
    "input",
    [
        {"foo": "bar", "baz": [{"eggs": []}]},
        {"foo": "bar", "baz": [{"eggs": {}}]},
        {"foo": "bar", "baz": [{"spam": "SPAM", "eggs": ""}]},
        {"foo": "bar", "baz": [{"eggs": None}]},
    ],
)
def test__strip_empty_json_paths_raises_exception(input):
    with pytest.raises(FhirValidationError):
        _strip_empty_json_paths(input, raise_on_discovery=True)


@pytest.mark.parametrize(
    "input",
    [
        {"foo": "bar", "baz": [{"eggs": ["spam"]}]},
        {"foo": "bar", "baz": [{"eggs": {"bam": "wap"}}]},
        {"foo": "bar", "baz": [{"eggs": "spam"}]},
        {"foo": "bar", "baz": [{"eggs": False}]},
    ],
)
def test__strip_empty_json_paths_do_not_raise(input):
    _strip_empty_json_paths(input, raise_on_discovery=True)


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


def test_transform_evaluation_key_to_next_page_token_throws_error():
    next_page_token = "INCORRECT"

    with pytest.raises(NextPageTokenValidationError):
        transform_next_page_token_to_start_key(next_page_token)
