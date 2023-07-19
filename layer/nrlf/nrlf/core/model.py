import re
from typing import Optional, Union

from aws_lambda_powertools.utilities.parser.models import (
    APIGatewayEventRequestContext as _APIGatewayEventRequestContext,
)
from aws_lambda_powertools.utilities.parser.models import (
    APIGatewayProxyEventModel as _APIGatewayProxyEventModel,
)
from pydantic import BaseModel, Field, Json, PrivateAttr, root_validator, validator

import nrlf.consumer.fhir.r4.model as consumer_model
import nrlf.producer.fhir.r4.model as producer_model
from nrlf.core.dynamodb_types import (
    DYNAMODB_NULL,
    DynamoDbDictType,
    DynamoDbIntType,
    DynamoDbListType,
    DynamoDbStringType,
    DynamoDbType,
    convert_dynamo_value_to_raw_value,
    is_dynamodb_dict,
)
from nrlf.core.errors import RequestValidationError
from nrlf.core.validators import (
    _get_tuple_components,
    create_document_type_tuple,
    generate_producer_id,
    split_custodian_id,
    validate_nhs_number,
    validate_producer_id,
    validate_source,
    validate_timestamp,
    validate_tuple,
)

from .constants import (
    CUSTODIAN_SEPARATOR,
    ID_SEPARATOR,
    KEY_SEPARATOR,
    TYPE_SEPARATOR,
    DbPrefix,
)

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
            f"Model {model.__class__.__name__} contains fields {bad_fields} that are not of type DynamoDbType"
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


def key(*args) -> str:
    """
    Standard method for creating PKs/SKs. Note that the "magic" here
    is that calling 'str()' on 'DynamoDbStringType' implicitly returns
    the __root__ value.
    """
    return KEY_SEPARATOR.join(map(str, args))


def dynamodb_key(*args) -> DynamoDbStringType:
    return DynamoDbStringType(__root__=key(*args))


def convert_document_pointer_id_to_pk(id: str) -> str:
    producer_id, document_id = _get_tuple_components(id, separator=ID_SEPARATOR)
    ods_code_parts = producer_id.split(CUSTODIAN_SEPARATOR)
    return key(DbPrefix.DocumentPointer, *ods_code_parts, document_id)


def split_pointer_type(pointer_type: str) -> tuple[str, str]:
    return pointer_type.split(TYPE_SEPARATOR)


class DocumentPointer(DynamoDbModel):
    id: DynamoDbStringType
    nhs_number: DynamoDbStringType
    custodian: DynamoDbStringType
    custodian_suffix: DynamoDbStringType = Field(default=DYNAMODB_NULL)
    producer_id: DynamoDbStringType
    type: DynamoDbStringType
    source: DynamoDbStringType
    version: DynamoDbIntType
    document: DynamoDbStringType
    created_on: DynamoDbStringType
    updated_on: Optional[DynamoDbStringType] = DYNAMODB_NULL
    document_id: DynamoDbStringType = Field(exclude=True)
    schemas: DynamoDbListType = Field(default_factory=DynamoDbListType)
    _document: dict = PrivateAttr()

    def __init__(self, *, _document=None, **data):
        super().__init__(**data)
        self._document = _document

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

    @property
    def pk(self) -> DynamoDbStringType:
        return dynamodb_key(
            DbPrefix.DocumentPointer, *self.custodian_parts, self.document_id
        )

    @property
    def sk(self) -> DynamoDbStringType:
        return self.pk

    @property
    def pk_1(self) -> DynamoDbStringType:
        return dynamodb_key(DbPrefix.Patient, self.nhs_number)

    @property
    def sk_1(self) -> DynamoDbStringType:
        return dynamodb_key(
            DbPrefix.CreatedOn,
            self.created_on,
            *self.custodian_parts,
            self.document_id,
        )

    @property
    def pk_2(self) -> DynamoDbStringType:
        return dynamodb_key(DbPrefix.Organization, *self.custodian_parts)

    @property
    def sk_2(self) -> DynamoDbStringType:
        return self.sk_1

    @property
    def custodian_parts(self) -> tuple[str]:
        return tuple(
            filter(None, (self.custodian.__root__, self.custodian_suffix.__root__))
        )

    @classmethod
    def public_alias(cls) -> str:
        return "DocumentReference"

    @root_validator(pre=True)
    def extract_custodian_suffix(cls, values: dict) -> dict:
        custodian: str = values.get("custodian")
        custodian_suffix: str = values.pop("custodian_suffix", None)
        if (custodian is not None) and (custodian_suffix is None):
            custodian, custodian_suffix = split_custodian_id(custodian)
            values["custodian"] = custodian
        if custodian_suffix is not None:
            values["custodian_suffix"] = custodian_suffix
        return values

    @root_validator(pre=True)
    def inject_producer_id(cls, values: dict) -> dict:
        producer_id = values.get("producer_id")
        if values.get("_from_dynamo"):
            producer_id = None

        producer_id, document_id = generate_producer_id(
            id=values.get("id"), producer_id=producer_id
        )

        values["producer_id"] = producer_id
        values["document_id"] = document_id
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

    @validator("producer_id")
    def validate_producer_id(value: DynamoDbStringType, values: dict) -> DynamoDbType:
        id: DynamoDbStringType = values.get("id")
        custodian: DynamoDbStringType = values.get("custodian_id")
        custodian_suffix: DynamoDbStringType = values.get("custodian_suffix")
        if not any(v is None for v in (id, custodian, custodian_suffix)):
            validate_producer_id(
                producer_id=value.__root__,
                id=id.__root__,
                custodian_id=custodian.__root__,
                custodian_suffix=custodian_suffix.__root__,
            )
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
        if value is None:
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


class CountRequestParams(consumer_model.CountRequestParams, _NhsNumberMixin):
    pass


class PaginatedResponse(BaseModel):
    last_evaluated_key: str = None
    items: list[BaseModel]


class Authorizer(BaseModel):
    pointer_types: Optional[Json[list[str]]] = Field(
        alias="pointer-types", default_factory=list
    )


class APIGatewayEventRequestContext(_APIGatewayEventRequestContext):
    authorizer: Optional[Authorizer] = Field(default_factory=Authorizer)


class APIGatewayProxyEventModel(_APIGatewayProxyEventModel):
    requestContext: APIGatewayEventRequestContext


class Contract(DynamoDbModel):
    pk: DynamoDbStringType
    sk: DynamoDbStringType
    name: DynamoDbStringType
    version: DynamoDbIntType
    system: DynamoDbStringType
    value: DynamoDbStringType
    json_schema: DynamoDbDictType

    @classmethod
    def kebab(cls) -> str:
        return "document-pointer"

    @property
    def full_name(self):
        return f"{self.name.__root__}:{self.version.__root__}"
