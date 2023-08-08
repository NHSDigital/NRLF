import json
from datetime import datetime as dt

from nhs_number import is_valid as is_valid_nhs_number
from pydantic import ValidationError

from nrlf.core.constants import (
    CUSTODIAN_SEPARATOR,
    ID_SEPARATOR,
    NHS_NUMBER_SYSTEM_URL,
    TYPE_SEPARATOR,
    VALID_SOURCES,
)
from nrlf.core.errors import (
    AuthenticationError,
    DocumentReferenceValidationError,
    DuplicateKeyError,
    FhirValidationError,
    InconsistentProducerId,
    InvalidTupleError,
    MalformedProducerId,
)
from nrlf.producer.fhir.r4.model import (
    CodeableConcept,
    DocumentReference,
    Identifier,
    RequestQueryType,
)


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
    return _get_tuple_components(tuple=id, separator=ID_SEPARATOR)


def create_document_type_tuple(document_type: CodeableConcept):
    try:
        (coding,) = document_type.coding
    except ValueError:
        n = len(document_type.coding)
        raise ValueError(
            f"Expected exactly one item in DocumentReference.type.coding, got {n}"
        ) from None
    return f"{coding.system}{TYPE_SEPARATOR}{coding.code}"


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
        DocumentReference(**json_loads(fhir_json))
    except (ValidationError, ValueError):
        raise DocumentReferenceValidationError(
            "There was a problem retrieving the document pointer"
        ) from None


def validate_type_system(type: RequestQueryType, pointer_types: list[str]):
    if type is not None:
        type_system = type.__root__.split("|", 1)[0]

        pointer_type_systems = map(
            lambda pointer_type: pointer_type.split("|", 1)[0], pointer_types
        )

        for pointer_type_system in pointer_type_systems:
            if type_system == pointer_type_system:
                return

        raise AuthenticationError(
            f"The provided system type value - {type_system} - does not match the allowed types"
        )


def validate_subject_identifier_system(subject_identifier: Identifier):
    if subject_identifier.system != NHS_NUMBER_SYSTEM_URL:
        raise FhirValidationError("Input FHIR JSON has an invalid subject:identifier")


def dict_raise_on_duplicates(list_of_pairs):
    checked_pairs = {}
    for k, v in list_of_pairs:
        if k in checked_pairs:
            raise DuplicateKeyError("Duplicate key: %r" % (k,))
        checked_pairs[k] = v
    return checked_pairs


def json_loads(json_string):
    return json.loads(json_string, object_pairs_hook=dict_raise_on_duplicates)


def json_load(json_file_obj):
    return json.load(json_file_obj, object_pairs_hook=dict_raise_on_duplicates)


def validate_producer_id(
    producer_id: str, custodian_id: str, custodian_suffix: str = None
):
    if custodian_suffix:
        if producer_id.split(CUSTODIAN_SEPARATOR) != (custodian_id, custodian_suffix):
            raise MalformedProducerId(
                f"Producer ID {producer_id} (extracted from '{id}') is not correctly formed. "
                "It is expected to be composed in the form '<custodian_id>.<custodian_suffix>'"
            )
    else:
        if producer_id != custodian_id:
            raise InconsistentProducerId(
                f"Producer ID {producer_id} (extracted from '{id}') "
                "does not match the Custodian ID."
            )


def split_custodian_id(custodian_id: str) -> dict:
    custodian_id_suffix = None
    try:
        custodian_id, custodian_id_suffix = custodian_id.split(CUSTODIAN_SEPARATOR)
    except ValueError:
        pass
    return custodian_id, custodian_id_suffix
