import base64
import json
from datetime import datetime as dt
from typing import Union

from more_itertools import map_except
from nrlf.core.constants import (
    EMPTY_VALUES,
    ID_SEPARATOR,
    JSON_TYPES,
    ODS_SYSTEM,
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
from nrlf.core.validators import validate_subject_identifier_system, json_loads
from nrlf.legacy.constants import LEGACY_SYSTEM, LEGACY_VERSION, NHS_NUMBER_SYSTEM_URL
from nrlf.legacy.model import LegacyDocumentPointer
from nrlf.producer.fhir.r4.model import Bundle, BundleEntry, DocumentReference, Meta
from nrlf.producer.fhir.r4.strict_model import (
    DocumentReference as StrictDocumentReference,
)
from pydantic import ValidationError


def make_timestamp() -> str:
    return dt.utcnow().isoformat(timespec="milliseconds") + "Z"


def _strip_empty_json_paths(
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
                        _strip_empty_json_paths(
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
            value = _strip_empty_json_paths(
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
        _strip_empty_json_paths(stripped_json, raise_on_discovery)
        if modified
        else stripped_json
    )


def _create_fhir_model_from_legacy_model(
    legacy_model: LegacyDocumentPointer, producer_id: str, nhs_number: str
) -> DocumentReference:
    return StrictDocumentReference(
        resourceType=DocumentReference.__name__,
        id=f"{producer_id}{ID_SEPARATOR}{legacy_model.logicalIdentifier.logicalId}",
        status=legacy_model.status,
        type={"coding": [legacy_model.type.dict()]},
        category=[legacy_model.class_.dict()],
        subject={"identifier": {"system": NHS_NUMBER_SYSTEM_URL, "value": nhs_number}},
        date=legacy_model.indexed.isoformat(),
        author=[legacy_model.author],
        custodian={
            "identifier": {
                "system": LEGACY_SYSTEM,
                "value": legacy_model.custodian.reference,
            }
        },
        relatesTo=[legacy_model.relatesTo] if legacy_model.relatesTo else [],
        content=legacy_model.content,
        context=legacy_model.context,
    )


def _create_legacy_model_from_legacy_json(legacy_json: dict) -> LegacyDocumentPointer:
    stripped_legacy_json = _strip_empty_json_paths(legacy_json)
    return LegacyDocumentPointer(**stripped_legacy_json)


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


def create_document_pointer_from_fhir_json(
    fhir_json: dict,
    api_version: int,
    source: Source = Source.NRLF,
    **kwargs,
) -> DocumentPointer:
    validate_required_create_fields(fhir_json)
    stripped_fhir_json = _strip_empty_json_paths(
        json=fhir_json, raise_on_discovery=True
    )
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
    validate_no_extra_fields(
        input_fhir_json=fhir_json,
        output_fhir_json=fhir_strict_model.dict(exclude_none=True),
    )
    validate_custodian_system(fhir_strict_model)
    validate_subject_identifier_system(
        subject_identifier=fhir_strict_model.subject.identifier
    )

    _strip_empty_json_paths(json=fhir_json, raise_on_discovery=True)
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


def create_document_pointer_from_legacy_json(
    legacy_json: dict, producer_id: str, nhs_number: str
) -> DocumentPointer:
    legacy_model = _create_legacy_model_from_legacy_json(legacy_json=legacy_json)
    fhir_model = _create_fhir_model_from_legacy_model(
        legacy_model=legacy_model, producer_id=producer_id, nhs_number=nhs_number
    )
    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_model.dict(exclude_none=True),
        api_version=LEGACY_VERSION,
        source=Source.LEGACY,
        created_on=legacy_model.lastModified.isoformat(),
        updated_on=legacy_model.lastModified.isoformat(),
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
