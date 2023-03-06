import re
from typing import Optional, Union

import nrlf.consumer.fhir.r4.model as consumer_model
import nrlf.producer.fhir.r4.model as producer_model
from nrlf.core.dynamodb_types import (
    DYNAMODB_NULL,
    DynamoDbIntType,
    DynamoDbStringType,
    DynamoDbType,
    convert_dynamo_value_to_raw_value,
    is_dynamodb_dict,
)
from nrlf.core.errors import RequestValidationError
from nrlf.core.validators import (
    create_document_type_tuple,
    generate_producer_id,
    validate_nhs_number,
    validate_source,
    validate_timestamp,
    validate_tuple,
)
from pydantic import BaseModel, Field, root_validator, validator

from .constants import ID_SEPARATOR, DbPrefix

KEBAB_CASE_RE = re.compile(r"(?<!^)(?=[A-Z])")


def to_kebab_case(name: str) -> str:
    return KEBAB_CASE_RE.sub("-", name).lower()


def assert_model_has_only_dynamodb_types(model: BaseModel):
    bad_fields = [
        field_name
        for field_name, field_value in model.__fields__.items()
        if not issubclass(field_value.type_, DynamoDbType)
    ]
    if bad_fields:
        raise TypeError(
            f"Model {model.__name__} contains fields {bad_fields} that are not of type DynamoDbType"
        )


class DynamoDbModel(BaseModel):
    _from_dynamo: bool = Field(
        default=False,
        exclude=True,
        description="internal flag for reading from dynamodb",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert_model_has_only_dynamodb_types(model=self)

    @root_validator(pre=True)
    def transform_input_values_if_dynamo_values(cls, values: dict) -> dict:
        from_dynamo = all(map(is_dynamodb_dict, values.values()))

        if from_dynamo:
            return {
                **{k: convert_dynamo_value_to_raw_value(v) for k, v in values.items()},
                "_from_dynamo": from_dynamo,
            }
        return values

    @classmethod
    def kebab(cls) -> str:
        return to_kebab_case(cls.__name__)

    @classmethod
    def public_alias(cls) -> str:
        return cls.__name__


KEY_SEPARATOR = "#"


def key(*args):
    """
    standard method for creating PKs/SKs
    """
    return KEY_SEPARATOR.join(map(lambda s: str(s), args))


class DocumentPointer(DynamoDbModel):
    id: DynamoDbStringType
    nhs_number: DynamoDbStringType
    custodian: DynamoDbStringType
    producer_id: DynamoDbStringType
    type: DynamoDbStringType
    source: DynamoDbStringType
    version: DynamoDbIntType
    document: DynamoDbStringType
    created_on: DynamoDbStringType
    updated_on: Optional[DynamoDbStringType] = DYNAMODB_NULL

    def dict(self, **kwargs):
        return {
            "pk": self.pk.dict(),
            "sk": self.sk.dict(),
            "pk_1": self.pk_1.dict(),
            "sk_1": self.sk_1.dict(),
            "pk_2": self.pk_2.dict(),
            "sk_2": self.sk_2.dict(),
            **super().dict(**kwargs),
        }

    def super_dict(self):
        return super().dict()

    @classmethod
    def generate_pk(cls, provider_id: str, document_id: str) -> str:
        return f"{DbPrefix.DocumentPointer}{KEY_SEPARATOR}{provider_id}{KEY_SEPARATOR}{document_id}"

    @classmethod
    def generate_id(cls, provider_id: str, document_id: str) -> str:
        return f"{provider_id}{ID_SEPARATOR}{document_id}"

    @classmethod
    def split_id(cls, id: str) -> list[str, str]:
        validate_tuple(id, ID_SEPARATOR)
        return f"{id}".split(ID_SEPARATOR, 1)

    @classmethod
    def split_pk(cls, pk: str) -> list[str, str]:
        return f"{pk}".split(KEY_SEPARATOR, 2)[1:]

    @classmethod
    def convert_id_to_pk(cls, id: str) -> str:
        (producer_id, document_id) = cls.split_id(id)
        return cls.generate_pk(producer_id, document_id)

    @classmethod
    def convert_pk_to_id(cls, pk: str) -> str:
        (producer_id, document_id) = cls.split_pk(pk)
        return cls.generate_id(producer_id, document_id)

    @property
    def doc_id(self) -> str:
        (_, doc_id) = f"{self.id}".split(ID_SEPARATOR)
        return doc_id

    @property
    def pk(self) -> DynamoDbStringType:
        return DynamoDbStringType(
            __root__=self.__class__.generate_pk(*self.__class__.split_id(f"{self.id}"))
        )

    @property
    def sk(self) -> DynamoDbStringType:
        return self.pk

    @property
    def pk_1(self) -> DynamoDbStringType:
        return DynamoDbStringType(__root__=f"{DbPrefix.Patient}#{self.nhs_number}")

    @property
    def sk_1(self) -> DynamoDbStringType:
        return DynamoDbStringType(
            __root__=f"{DbPrefix.CreatedOn}#{self.created_on}#{self.producer_id}#{self.doc_id}"
        )

    @property
    def pk_2(self) -> DynamoDbStringType:
        return DynamoDbStringType(
            __root__=f"{DbPrefix.Organization}#{self.producer_id}"
        )

    @property
    def sk_2(self) -> DynamoDbStringType:
        return self.sk_1

    @classmethod
    def public_alias(cls) -> str:
        return "DocumentReference"

    @root_validator(pre=True)
    def inject_producer_id(cls, values: dict) -> dict:
        if values.get("_from_dynamo"):
            return values

        producer_id = generate_producer_id(
            id=values.get("id"), producer_id=values.get("producer_id")
        )
        values["producer_id"] = producer_id
        return values

    @root_validator(pre=True)
    def coerce_document_type_to_tuple(cls, values: dict) -> dict:
        if values.get("_from_dynamo"):
            return values

        document_type_tuple = create_document_type_tuple(
            document_type=values.get("type")
        )
        values["type"] = document_type_tuple
        return values

    @validator("id")
    def validate_id(value: any) -> DynamoDbType:
        validate_tuple(tuple=value.__root__, separator=ID_SEPARATOR)
        return value

    @validator("type")
    def validate_type(value: any) -> DynamoDbType:
        validate_tuple(tuple=value.__root__, separator="|")
        return value

    @validator("nhs_number")
    def validate_nhs_number(value: any) -> DynamoDbType:
        validate_nhs_number(nhs_number=value.__root__)
        return value

    @validator("source")
    def validate_source(value: any) -> DynamoDbType:
        validate_source(source=value.__root__)
        return value

    @validator("created_on")
    def validate_created_on(value: any) -> DynamoDbType:
        validate_timestamp(date=value.__root__)
        return value

    @validator("updated_on")
    def validate_updated_on(value: any) -> DynamoDbType:
        if value == None:
            return DYNAMODB_NULL

        validate_timestamp(date=value.__root__)
        return value


class _NhsNumberMixin:
    @property
    def nhs_number(self) -> Union[str, None]:
        if self.subject_identifier is None:
            return None
        try:
            nhs_number = self.subject_identifier.__root__.split("|", 1)[1]
            validate_nhs_number(nhs_number)
            return nhs_number
        except ValueError as e:
            raise RequestValidationError(e)


class ProducerRequestParams(producer_model.RequestParams, _NhsNumberMixin):
    pass


class ConsumerRequestParams(consumer_model.RequestParams, _NhsNumberMixin):
    pass
