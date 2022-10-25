import json
from datetime import datetime as dt
from typing import Union

from nrlf.core.constants import EMPTY_VALUES, JSON_TYPES, Source
from nrlf.core.model import DocumentPointer
from nrlf.legacy.constants import LEGACY_SYSTEM, LEGACY_VERSION, NHS_NUMBER_SYSTEM_URL
from nrlf.legacy.model import LegacyDocumentPointer
from nrlf.producer.fhir.r4.model import DocumentReference


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
    return DocumentReference(
        resourceType=DocumentReference.__name__,
        masterIdentifier={
            "system": LEGACY_SYSTEM,
            "value": f"{producer_id}|{legacy_model.logicalIdentifier.logicalId}",
        },
        status=legacy_model.status,
        type={"coding": [legacy_model.type.dict()]},
        category=[legacy_model.class_.dict()],
        subject={"system": NHS_NUMBER_SYSTEM_URL, "id": nhs_number},
        date=legacy_model.indexed.isoformat(),
        author=[legacy_model.author],
        custodian={"system": LEGACY_SYSTEM, "id": legacy_model.custodian.reference},
        relatesTo=[legacy_model.relatesTo] if legacy_model.relatesTo else [],
        content=legacy_model.content,
        context=legacy_model.context,
    )


def _create_legacy_model_from_legacy_json(legacy_json: dict) -> LegacyDocumentPointer:
    stripped_legacy_json = _strip_empty_json_paths(legacy_json)
    return LegacyDocumentPointer(**stripped_legacy_json)


def create_document_pointer_from_fhir_json(
    fhir_json: dict, api_version: int, source: Source = Source.NRLF, **kwargs
) -> DocumentPointer:
    fhir_model = DocumentReference(**fhir_json)
    core_model = DocumentPointer(
        id=fhir_model.masterIdentifier.value,
        nhs_number=fhir_model.subject.id,
        type=fhir_model.type,
        version=api_version,
        document=fhir_json,
        source=source.value,
        created_on=kwargs.pop("created_on", make_timestamp()),
        **kwargs,
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
