import json
from datetime import datetime as dt
from typing import Union

from more_itertools import map_except
from nrlf.core.constants import EMPTY_VALUES, ID_SEPARATOR, JSON_TYPES, Source
from nrlf.core.errors import FhirValidationError
from nrlf.core.model import DocumentPointer
from nrlf.legacy.constants import LEGACY_SYSTEM, LEGACY_VERSION, NHS_NUMBER_SYSTEM_URL
from nrlf.legacy.model import LegacyDocumentPointer
from nrlf.producer.fhir.r4.model import Bundle, BundleEntry, DocumentReference
from nrlf.producer.fhir.r4.strict_model import (
    DocumentReference as StrictDocumentReference,
)
from pydantic import ValidationError


def make_timestamp() -> str:
    return dt.utcnow().isoformat(timespec="milliseconds") + "Z"


def _strip_empty_json_paths(json: Union[list[dict], dict]) -> Union[list[dict], dict]:
    if json in EMPTY_VALUES:
        return None

    if type(json) is list:
        if type(json[0]) is dict:
            return list(filter(None, (_strip_empty_json_paths(item) for item in json)))
        return json

    stripped_json = {}
    modified = False
    for key, value in json.items():
        if type(value) in JSON_TYPES:
            value = _strip_empty_json_paths(value)
        if value in EMPTY_VALUES:
            modified = True
            continue
        stripped_json[key] = value

    return _strip_empty_json_paths(stripped_json) if modified else stripped_json


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
        print("input fhir", input_fhir_json)
        print("output_fhir_json", output_fhir_json)
        raise FhirValidationError("Input FHIR JSON has additional non-FHIR fields.")


def create_document_pointer_from_fhir_json(
    fhir_json: dict,
    api_version: int,
    source: Source = Source.NRLF,
    **kwargs,
) -> DocumentPointer:
    fhir_model = create_fhir_model_from_fhir_json(fhir_json=fhir_json)
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
        lambda document_pointer: json.loads(document_pointer.document.__root__),
        document_pointers,
    )

    document_references = map_except(
        lambda document_json: DocumentReference(**document_json),
        document_pointer_jsons,
        ValidationError,
    )

    return [BundleEntry(resource=reference) for reference in document_references]


def create_bundle_from_document_pointers(
    document_pointers: list[DocumentPointer],
) -> Bundle:

    bundleEntryList = create_bundle_entries_from_document_pointers(document_pointers)

    return Bundle(
        resourceType="Bundle",
        type="searchset",
        total=len(bundleEntryList),
        entry=bundleEntryList,
    ).dict(exclude_none=True, exclude_defaults=True)
