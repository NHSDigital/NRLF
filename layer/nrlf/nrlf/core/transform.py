import base64
import json
from datetime import datetime as dt
from typing import Union

from more_itertools import map_except
from pydantic import ValidationError

from nrlf.core.constants import (
    ALLOWED_RELATES_TO_CODES,
    EMPTY_VALUES,
    JSON_TYPES,
    ODS_SYSTEM,
    RELATES_TO_REPLACES,
    REQUIRED_CREATE_FIELDS,
    Source,
)
from nrlf.core.errors import (
    FhirValidationError,
    MissingRequiredFieldForCreate,
    NextPageTokenValidationError,
    ProducerCreateValidationError,
    RequestValidationError,
)
from nrlf.core.model import DocumentPointer, PaginatedResponse
from nrlf.core.validators import json_loads, validate_subject_identifier_system
from nrlf.producer.fhir.r4.model import (
    Bundle,
    BundleEntry,
    DocumentReference,
    DocumentReferenceRelatesTo,
    Meta,
)
from nrlf.producer.fhir.r4.strict_model import (
    DocumentReference as StrictDocumentReference,
)


def make_timestamp() -> str:
    return dt.utcnow().isoformat(timespec="milliseconds") + "Z"


def strip_empty_json_paths(
    json: Union[list[dict], dict], raise_on_discovery=False, json_path: list = None
) -> Union[list[dict], dict]:
    if json_path is None:
        json_path = []

    if json in EMPTY_VALUES:
        if raise_on_discovery:
            if json in REQUIRED_CREATE_FIELDS:
                raise ProducerCreateValidationError(
                    f"DocumentReference validation failure - Invalid value '{json}' at {'.'.join(json_path)}"
                )
            raise FhirValidationError(
                f"Empty value '{json}' at '{'.'.join(json_path)}' is not valid FHIR"
            )
        return None

    if type(json) is list:
        if type(json[0]) is dict:
            return list(
                filter(
                    None,
                    (
                        strip_empty_json_paths(
                            item, raise_on_discovery, json_path=json_path + [str(i)]
                        )
                        for i, item in enumerate(json)
                    ),
                )
            )
        return json

    stripped_json = {}
    modified = False
    for key, value in json.items():
        if type(value) in JSON_TYPES:
            value = strip_empty_json_paths(
                value, raise_on_discovery, json_path=json_path + [key]
            )
        if value in EMPTY_VALUES:
            modified = True
            if raise_on_discovery:
                if key in REQUIRED_CREATE_FIELDS:
                    raise ProducerCreateValidationError(
                        f"DocumentReference validation failure - Invalid '{value}' at {'.'.join(json_path + [key])} "
                    )
                raise FhirValidationError(
                    f"Empty value '{value}' at '{'.'.join(json_path + [key])}' is not valid FHIR"
                )
            continue
        stripped_json[key] = value
    return (
        strip_empty_json_paths(stripped_json, raise_on_discovery)
        if modified
        else stripped_json
    )


def validate_no_extra_fields(input_fhir_json, output_fhir_json):
    if input_fhir_json != output_fhir_json:
        raise FhirValidationError("Input FHIR JSON has additional non-FHIR fields.")


def validate_required_create_fields(request_body_json):
    for field in REQUIRED_CREATE_FIELDS:
        if field not in request_body_json:
            raise MissingRequiredFieldForCreate(
                f"The required field {field} is missing"
            )


def validate_custodian_system(fhir_strict_model: StrictDocumentReference):
    if fhir_strict_model.custodian.identifier.system != ODS_SYSTEM:
        raise RequestValidationError(
            "Provided custodian identifier system is not the ODS system"
        )


def validate_relates_to(relates_to: list[DocumentReferenceRelatesTo]):
    for document_reference_relates_to in relates_to:
        if document_reference_relates_to.code not in ALLOWED_RELATES_TO_CODES:
            raise RequestValidationError(
                f"Provided relatesTo code '{document_reference_relates_to.code}' must be one of {sorted(ALLOWED_RELATES_TO_CODES)}"
            )
        if document_reference_relates_to.code == RELATES_TO_REPLACES and not (
            document_reference_relates_to.target.identifier
            and document_reference_relates_to.target.identifier.value
        ):
            raise RequestValidationError(
                "'relatesTo.target.identifier.value' must be specified when "
                f"relatesTo.code is '{RELATES_TO_REPLACES}'"
            )


def create_document_pointer_from_fhir_json(
    fhir_json: dict,
    api_version: int,
    source: Source = Source.NRLF,
    **kwargs,
) -> DocumentPointer:
    stripped_fhir_json = strip_empty_json_paths(json=fhir_json, raise_on_discovery=True)
    fhir_model = create_fhir_model_from_fhir_json(fhir_json=stripped_fhir_json)
    core_model = DocumentPointer(
        id=fhir_model.id,
        nhs_number=fhir_model.subject.identifier.value,
        custodian=fhir_model.custodian.identifier.value,
        type=fhir_model.type,
        version=api_version,
        document=json.dumps(fhir_json),
        source=source.value,
        created_on=kwargs.pop("created_on", make_timestamp()),
        **kwargs,
    )
    return core_model


def create_fhir_model_from_fhir_json(fhir_json: dict) -> StrictDocumentReference:
    DocumentReference(**fhir_json)
    fhir_strict_model = StrictDocumentReference(**fhir_json)
    validate_required_create_fields(fhir_json)
    validate_no_extra_fields(
        input_fhir_json=fhir_json,
        output_fhir_json=fhir_strict_model.dict(exclude_none=True),
    )
    validate_custodian_system(fhir_strict_model)
    validate_subject_identifier_system(
        subject_identifier=fhir_strict_model.subject.identifier
    )

    strip_empty_json_paths(json=fhir_json, raise_on_discovery=True)
    if fhir_strict_model.relatesTo:
        validate_relates_to(relates_to=fhir_strict_model.relatesTo)
    return fhir_strict_model


def update_document_pointer_from_fhir_json(
    fhir_json: dict, api_version: int, source: Source = Source.NRLF, **kwargs
) -> DocumentPointer:
    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json,
        api_version=api_version,
        source=source,
        created_on=kwargs.pop("created_on", make_timestamp()),
        updated_on=kwargs.pop("updated_on", make_timestamp()),
    )
    return core_model


def create_bundle_entries_from_document_pointers(
    document_pointers: list[DocumentPointer],
) -> list[BundleEntry]:
    document_pointer_jsons = map(
        lambda document_pointer: json_loads(document_pointer.document.__root__),
        document_pointers,
    )

    document_references = map_except(
        lambda document_json: DocumentReference(**document_json),
        document_pointer_jsons,
        ValidationError,
    )

    return [BundleEntry(resource=reference) for reference in document_references]


def create_bundle_count(count: int) -> Bundle:
    bundle_dict = dict(
        resourceType="Bundle",
        type="searchset",
        total=count,
        entry=[],
    )
    return Bundle(**bundle_dict).dict(exclude_none=True, exclude_defaults=True)


def create_bundle_from_paginated_response(
    paginated_response: PaginatedResponse,
) -> Bundle:
    document_pointers = paginated_response.document_pointers

    bundleEntryList = create_bundle_entries_from_document_pointers(document_pointers)
    bundle_dict = dict(
        resourceType="Bundle",
        type="searchset",
        total=len(bundleEntryList),
        entry=bundleEntryList,
    )

    if paginated_response.last_evaluated_key is not None:
        last_evaluated_key = paginated_response.last_evaluated_key
        bundle_dict["meta"] = create_meta(last_evaluated_key)

    return Bundle(**bundle_dict).dict(exclude_none=True, exclude_defaults=True)


def create_meta(last_evaluated_key: object) -> Meta:
    last_key = str(last_evaluated_key)

    coding = {"code": last_key, "display": "next_page_token"}

    return {"tag": [coding]}


def transform_evaluation_key_to_next_page_token(last_evaluated_key: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(last_evaluated_key).encode()).decode()


def transform_next_page_token_to_start_key(exclusive_start_key: str) -> dict:
    try:
        return json_loads(base64.urlsafe_b64decode(exclusive_start_key))
    except Exception:
        raise NextPageTokenValidationError("Unable to decode the next page token")
