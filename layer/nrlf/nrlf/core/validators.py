import json
from datetime import datetime as dt

from nhs_number import is_valid as is_valid_nhs_number
from nrlf.core.constants import ID_SEPARATOR, VALID_SOURCES
from nrlf.core.errors import (
    DocumentReferenceValidationError,
    InvalidTupleError,
    RequestValidationError,
)
from nrlf.producer.fhir.r4.model import CodeableConcept, DocumentReference
from nrlf.producer.fhir.r4.strict_model import (
    DocumentReference as StrictDocumentReference,
)
from pydantic import ValidationError


def _get_tuple_components(tuple: str, separator: str) -> tuple[str, str]:
    try:
        a, b = tuple.split(separator, 1)
    except ValueError:
        raise InvalidTupleError(
            f"Input is not composite of the form a{separator}b: {tuple}"
        ) from None
    return a, b


def generate_producer_id(id: str, producer_id: str) -> str:
    if producer_id:
        raise ValueError(
            "producer_id should not be passed to DocumentPointer; "
            "it will be extracted from id."
        )
    producer_id, _ = _get_tuple_components(tuple=id, separator=ID_SEPARATOR)
    return producer_id


def create_document_type_tuple(document_type: CodeableConcept):
    try:
        (coding,) = document_type.coding
    except ValueError:
        n = len(document_type.coding)
        raise ValueError(
            f"Expected exactly one item in DocumentReference.type.coding, got {n}"
        ) from None
    return f"{coding.system}|{coding.code}"


def validate_nhs_number(nhs_number: str):
    if not is_valid_nhs_number(nhs_number):
        raise ValueError(f"Not a valid NHS Number: {nhs_number}")


def validate_tuple(tuple: str, separator: str):
    _get_tuple_components(tuple=tuple, separator=separator)


def validate_source(source: str):
    if source not in VALID_SOURCES:
        raise ValueError(f"Not a source: {source}. Expected one of {VALID_SOURCES}.")


def validate_timestamp(date: str):
    _date = date[:-1] if date.endswith("Z") else date
    try:
        dt.fromisoformat(_date)
    except ValueError:
        raise ValueError(f"Not a valid ISO date: {date}") from None


def requesting_application_is_not_authorised(
    requesting_application_id, authenticated_application_id
):
    return requesting_application_id != authenticated_application_id


def validate_document_reference_string(fhir_json: str):
    try:
        DocumentReference(**json.loads(fhir_json))
    except ValidationError:
        raise DocumentReferenceValidationError("Item could not be found")
    except ValueError:
        raise DocumentReferenceValidationError("Item could not be found")


def validate_fhir_model_for_required_fields(model: StrictDocumentReference):

    if not model.custodian:
        raise RequestValidationError(
            "DocumentReference validation failure - Invalid custodian"
        )
