import json
from datetime import datetime as dt
from typing import Optional

from nrlf.core.dynamodb_types import DYNAMODB_NULL, DynamoDbType
from nrlf.core.validators import (
    create_document_type_tuple,
    generate_producer_id,
    validate_tuple,
    validate_nhs_number,
    validate_status,
    validate_timestamp,
    make_timestamp,
)
from nrlf.producer.fhir.r4.model import DocumentReference
from pydantic import BaseModel, root_validator, validator


class DocumentPointer(BaseModel):
    id: DynamoDbType[str]
    nhs_number: DynamoDbType[str]
    producer_id: DynamoDbType[str]
    type: DynamoDbType[str]
    status: DynamoDbType[str]
    version: DynamoDbType[int]
    document: DynamoDbType[dict]
    created_on: DynamoDbType[str]
    updated_on: Optional[DynamoDbType[str]] = DYNAMODB_NULL
    deleted_on: Optional[DynamoDbType[str]] = DYNAMODB_NULL

    @root_validator(pre=True)
    def inject_producer_id(cls, values: dict) -> dict:
        producer_id = generate_producer_id(
            id=values.get("id"), producer_id=values.get("producer_id")
        )
        values["producer_id"] = producer_id
        return values

    @root_validator(pre=True)
    def coerce_document_type_to_tuple(cls, values: dict) -> dict:
        document_type_tuple = create_document_type_tuple(
            document_type=values.get("type")
        )
        values["type"] = document_type_tuple
        return values

    @root_validator(pre=True)
    def convert_to_dynamodb_format(cls, values: dict) -> dict:
        for k, v in values.items():
            _type = DynamoDbType[type(v)]
            values[k] = _type(value=v)
        return values

    @validator("id", "type")
    def validate_tuple(value: any) -> DynamoDbType[str]:
        validate_tuple(tuple=value.raw_value)
        return value

    @validator("nhs_number")
    def validate_nhs_number(value: any) -> DynamoDbType[str]:
        validate_nhs_number(nhs_number=value.raw_value)
        return value

    @validator("status")
    def validate_status(value: any) -> DynamoDbType[str]:
        validate_status(status=value.raw_value)
        return value

    @validator("created_on", "updated_on", "deleted_on")
    def validate_timestamp(value: any) -> DynamoDbType[str]:
        validate_timestamp(date=value.raw_value)
        return value


def create_document_pointer_from_fhir_json(
    raw_fhir_json: str, api_version: int
) -> DocumentPointer:
    fhir_json = json.loads(raw_fhir_json)
    fhir_model = DocumentReference(**fhir_json)
    core_model = DocumentPointer(
        id=fhir_model.masterIdentifier.value,
        nhs_number=fhir_model.subject.id,
        type=fhir_model.type,
        status=fhir_model.status,
        version=api_version,
        document=fhir_json,
        created_on=make_timestamp(),
    )
    return core_model
