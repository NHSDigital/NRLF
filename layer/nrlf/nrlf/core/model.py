import json
from nrlf.core.dynamodb_types import DynamoDbType
from nrlf.core.validators import (
    validate_document,
    validate_id,
    validate_nhs_number,
    validate_status,
)
from nrlf.producer.fhir.r4.model import DocumentReference
from pydantic import BaseModel, root_validator, validator


class DocumentPointer(BaseModel):
    producer_id: DynamoDbType[str]
    id: DynamoDbType[str]
    nhs_number: DynamoDbType[str]
    status: DynamoDbType[str]
    version: DynamoDbType[int]
    raw_document: DynamoDbType[str]
    validated_document: DynamoDbType[str]

    @root_validator(pre=True)
    def convert_to_dynamodb_format(cls, values):
        for k, v in values.items():
            _type = DynamoDbType[type(v)]
            values[k] = _type(value=v)
        return values

    @validator("id")
    def validate_id(value: any, values: dict) -> DynamoDbType[str]:
        validate_id(id=value.raw_value, producer_id=values.get("producer_id").raw_value)
        return value

    @validator("nhs_number")
    def validate_nhs_number(value: any) -> DynamoDbType[str]:
        validate_nhs_number(nhs_number=value.raw_value)
        return value

    @validator("status")
    def validate_status(value: any) -> DynamoDbType[str]:
        validate_status(status=value.raw_value)
        return value

    @validator("raw_document", "validated_document")
    def validate_document(value: any) -> DynamoDbType[str]:
        validate_document(document=value.raw_value)
        return value


def fhir_to_core(raw_document: str, api_version: int) -> DocumentPointer:
    fhir_json = json.loads(raw_document)
    fhir_model = DocumentReference(**fhir_json)
    core_model = DocumentPointer(
        id=fhir_model.masterIdentifier.value,
        nhs_number=fhir_model.subject.id,
        producer_id=fhir_model.custodian.id,
        status=fhir_model.status,
        version=api_version,
        raw_document=raw_document,
        validated_document=fhir_model.json(exclude_none=True),
    )
    return core_model
