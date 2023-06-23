import pytest
from pydantic import BaseModel

from nrlf.core.constants import REQUIRED_CREATE_FIELDS
from nrlf.core.errors import (
    FhirValidationError,
    MissingRequiredFieldForCreate,
    NextPageTokenValidationError,
    ProducerCreateValidationError,
    RequestValidationError,
)
from nrlf.core.transform import (
    create_bundle_entries_from_document_pointers,
    create_document_pointer_from_fhir_json,
    strip_empty_json_paths,
    transform_next_page_token_to_start_key,
    validate_custodian_system,
    validate_no_extra_fields,
    validate_required_create_fields,
)
from nrlf.producer.fhir.r4.model import BundleEntry, DocumentReference
from nrlf.producer.fhir.r4.strict_model import (
    DocumentReference as StrictDocumentReference,
)
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data


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
    assert strip_empty_json_paths(input) == expected


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
        strip_empty_json_paths(input, raise_on_discovery=True)


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
    strip_empty_json_paths(input, raise_on_discovery=True)


@pytest.mark.parametrize("field", REQUIRED_CREATE_FIELDS)
def test_strip_empty_json_paths_throws_error_when_field_missing(field):
    fhir_json = read_test_data("nrlf")
    fhir_json[field] = None

    with pytest.raises(ProducerCreateValidationError):
        strip_empty_json_paths(fhir_json, raise_on_discovery=True)


def test_strip_empty_json_paths_throws_error_when_field_missing():
    assert REQUIRED_CREATE_FIELDS == ["custodian", "id", "type", "status", "subject"]


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


@pytest.mark.parametrize("field", REQUIRED_CREATE_FIELDS)
def test_validate_required_create_fields(field):
    fhir_json = read_test_data("nrlf")
    fhir_json.pop(field)

    with pytest.raises(MissingRequiredFieldForCreate):
        validate_required_create_fields(fhir_json)


def test_validate_custodian_system():
    fhir_json = read_test_data("nrlf")
    fhir_strict_model = StrictDocumentReference(**fhir_json)

    assert validate_custodian_system(fhir_strict_model) == None


def test_validate_custodian_system_fails():
    fhir_json = read_test_data("nrlf")
    fhir_json["custodian"]["identifier"]["system"] = "wrong/system"
    fhir_strict_model = StrictDocumentReference(**fhir_json)

    with pytest.raises(RequestValidationError):
        validate_custodian_system(fhir_strict_model)
