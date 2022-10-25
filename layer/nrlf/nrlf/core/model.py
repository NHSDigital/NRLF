from typing import Optional

from nrlf.core.dynamodb_types import DYNAMODB_NULL, DynamoDbType
from nrlf.core.validators import (
    create_document_type_tuple,
    generate_producer_id,
    validate_nhs_number,
    validate_source,
    validate_timestamp,
    validate_tuple,
)
from pydantic import BaseModel, root_validator, validator


def assert_model_has_only_dynamodb_types(model: BaseModel):
    bad_fields = [
        field_name
        for field_name, field_value in model.__fields__.items()
        if not issubclass(field_value.type_, DynamoDbType)
    ]
    if bad_fields:
        raise TypeError(
            f"Model contains fields {bad_fields} that are not of type DynamoDbType"
        )


class DocumentPointer(BaseModel):
    id: DynamoDbType[str]
    nhs_number: DynamoDbType[str]
    producer_id: DynamoDbType[str]
    type: DynamoDbType[str]
    source: DynamoDbType[str]
    version: DynamoDbType[int]
    document: DynamoDbType[dict]
    created_on: DynamoDbType[str]
    updated_on: Optional[DynamoDbType[str]] = DYNAMODB_NULL

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

    @validator("source")
    def validate_source(value: any) -> DynamoDbType[str]:
        validate_source(source=value.raw_value)
        return value

    @validator("created_on", "updated_on")
    def validate_timestamp(value: any) -> DynamoDbType[str]:
        validate_timestamp(date=value.raw_value)
        return value
