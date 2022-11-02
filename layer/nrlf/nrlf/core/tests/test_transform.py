import pytest
from nrlf.core.errors import FhirValidationError
from nrlf.core.model import DocumentPointer
from nrlf.core.transform import (
    create_document_pointer_from_fhir_json,
    create_document_references_from_document_pointers,
    validate_no_extra_fields,
)
from nrlf.producer.fhir.r4.model import DocumentReference
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
    expected_reference = [DocumentReference(**fhir_json)]
    result = create_document_references_from_document_pointers([core_model])

    assert result == expected_reference
