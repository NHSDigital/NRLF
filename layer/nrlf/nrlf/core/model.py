import inspect
import re
from typing import Dict, Optional, Type, Union, get_origin

from aws_lambda_powertools.utilities.parser.models import (
    APIGatewayEventRequestContext as _APIGatewayEventRequestContext,
)
from aws_lambda_powertools.utilities.parser.models import (
    APIGatewayProxyEventModel as _APIGatewayProxyEventModel,
)
from pydantic import (
    BaseModel,
    Field,
    Json,
    PrivateAttr,
    RootModel,
    ValidationInfo,
    computed_field,
    field_validator,
    model_validator,
)

import nrlf.consumer.fhir.r4.model as consumer_model
import nrlf.producer.fhir.r4.model as producer_model
from nrlf.core.dynamodb_types import (
    DYNAMODB_NULL,
    DynamoDbDictType,
    DynamoDbIntType,
    DynamoDbListType,
    DynamoDbNullType,
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


def inherits_from(child: Optional[Type], parent: Type) -> bool:
    if inspect.isclass(child):
        if parent.__name__ in [c.__name__ for c in inspect.getmro(child)[1:]]:
            return True

    if get_origin(child) == Union:
        return any(inherits_from(subtype, parent) for subtype in child.__args__)

    return False


def assert_model_has_only_dynamodb_types(model: Type[BaseModel]):
    bad_fields = [
        field_name
        for field_name, field_value in model.model_fields.items()
        if not inherits_from(field_value.annotation, DynamoDbType)
    ]
    if bad_fields:
        raise TypeError(
            f"Model {model.__name__} contains fields {bad_fields} that are not of type DynamoDbType"
        )


class DynamoDbModel(BaseModel):
    _from_dynamo: bool = PrivateAttr(
        default=False
    )  # internal flag for reading from dynamodb

    def __init__(self, **kwargs):
        model_data = self.transform_input_values_if_dynamo_values(kwargs)
        super().__init__(**model_data)
        assert_model_has_only_dynamodb_types(model=self.__class__)

    @classmethod
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
    the rootue.
    """
    return KEY_SEPARATOR.join(map(str, args))


def dynamodb_key(*args) -> DynamoDbStringType:
    return DynamoDbStringType(root=key(*args))


def convert_document_pointer_id_to_pk(id: str) -> str:
    producer_id, document_id = _get_tuple_components(id, separator=ID_SEPARATOR)
    ods_code_parts = producer_id.split(CUSTODIAN_SEPARATOR)
    return key(DbPrefix.DocumentPointer, *ods_code_parts, document_id)


def split_pointer_type(pointer_type: str) -> tuple[str, ...]:
    return tuple(pointer_type.split(TYPE_SEPARATOR))


class DocumentPointer(DynamoDbModel):
    id: DynamoDbStringType
    nhs_number: DynamoDbStringType
    custodian: DynamoDbStringType
    custodian_suffix: Union[DynamoDbStringType, DynamoDbNullType] = Field(
        default=DYNAMODB_NULL
    )
    producer_id: DynamoDbStringType
    type: DynamoDbStringType
    source: DynamoDbStringType
    version: DynamoDbIntType
    document: DynamoDbStringType
    created_on: DynamoDbStringType
    updated_on: Union[DynamoDbStringType, DynamoDbNullType] = DYNAMODB_NULL
    document_id: DynamoDbStringType = Field(exclude=True)
    schemas: DynamoDbListType = Field(default_factory=DynamoDbListType)
    _document: dict = PrivateAttr()

    def __init__(self, *, _document=None, **data):
        super().__init__(**data)
        self._document = _document

    @computed_field
    @property
    def pk(self) -> DynamoDbStringType:
        return dynamodb_key(
            DbPrefix.DocumentPointer, *self.custodian_parts, self.document_id
        )

    @computed_field
    @property
    def sk(self) -> DynamoDbStringType:
        return self.pk

    @computed_field
    @property
    def pk_1(self) -> DynamoDbStringType:
        return dynamodb_key(DbPrefix.Patient, self.nhs_number)

    @computed_field
    @property
    def sk_1(self) -> DynamoDbStringType:
        return dynamodb_key(
            DbPrefix.CreatedOn,
            self.created_on,
            *self.custodian_parts,
            self.document_id,
        )

    @computed_field
    @property
    def pk_2(self) -> DynamoDbStringType:
        return dynamodb_key(DbPrefix.Organization, *self.custodian_parts)

    @computed_field
    @property
    def sk_2(self) -> DynamoDbStringType:
        return self.sk_1

    @property
    def custodian_parts(self) -> tuple[str, ...]:
        return tuple(filter(None, (self.custodian.root, self.custodian_suffix.root)))

    @classmethod
    def public_alias(cls) -> str:
        return "DocumentReference"

    @model_validator(mode="before")
    @classmethod
    def extract_custodian_suffix(cls, values: Dict) -> Dict:
        custodian = values.get("custodian")
        custodian_suffix = values.get("custodian_suffix")

        if (custodian is not None) and (custodian_suffix is None):
            custodian, custodian_suffix = split_custodian_id(custodian)
            values["custodian"] = custodian

        if custodian_suffix is not None:
            values["custodian_suffix"] = custodian_suffix

        return values

    @model_validator(mode="before")
    @classmethod
    def inject_producer_id(cls, values: Dict) -> Dict:
        producer_id = values.get("producer_id")
        if values.get("_from_dynamo"):
            producer_id = None

        producer_id, document_id = generate_producer_id(
            id=values.get("id"), producer_id=producer_id
        )

        values["producer_id"] = producer_id
        values["document_id"] = document_id
        return values

    @model_validator(mode="before")
    @classmethod
    def coerce_document_type_to_tuple(cls, values: Dict) -> Dict:
        if values.get("_from_dynamo"):
            return values

        document_type_tuple = create_document_type_tuple(
            document_type=values.get("type")
        )
        values["type"] = document_type_tuple
        return values

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: DynamoDbStringType) -> DynamoDbStringType:
        validate_tuple(tuple=value.root, separator=ID_SEPARATOR)
        return value

    @field_validator("producer_id")
    def validate_producer_id(
        cls, value: DynamoDbStringType, info: ValidationInfo
    ) -> DynamoDbType:
        id: Optional[DynamoDbStringType] = info.data.get("id")
        custodian: Optional[DynamoDbStringType] = info.data.get("custodian")
        custodian_suffix: Optional[DynamoDbStringType] = info.data.get(
            "custodian_suffix"
        )

        if id and custodian and custodian_suffix:
            validate_producer_id(
                producer_id=value.root,
                custodian_id=custodian.root,
                custodian_suffix=custodian_suffix.root,
            )

        return value

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: DynamoDbStringType) -> DynamoDbStringType:
        validate_tuple(tuple=value.root, separator="|")
        return value

    @field_validator("nhs_number")
    @classmethod
    def validate_nhs_number(cls, value: DynamoDbStringType) -> DynamoDbStringType:
        validate_nhs_number(nhs_number=value.root)
        return value

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: DynamoDbStringType) -> DynamoDbStringType:
        validate_source(source=value.root)
        return value

    @field_validator("created_on")
    @classmethod
    def validate_created_on(cls, value: DynamoDbStringType) -> DynamoDbStringType:
        validate_timestamp(date=value.root)
        return value

    @field_validator("updated_on")
    @classmethod
    def validate_updated_on(cls, value: DynamoDbStringType) -> DynamoDbType:
        if not value or value.root is None:
            return DYNAMODB_NULL

        validate_timestamp(date=value.root)
        return value


class _NhsNumberMixin:
    subject_identifier: RootModel

    @property
    def nhs_number(self) -> Union[str, None]:
        if self.subject_identifier is None:
            return None
        try:
            nhs_number = self.subject_identifier.root.split("|", 1)[1]
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
    last_evaluated_key: Optional[str] = None
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
    version: DynamoDbStringType
    system: DynamoDbStringType
    value: DynamoDbStringType
    json_schema: DynamoDbDictType

    @classmethod
    def kebab(cls) -> str:
        return "document-pointer"

    @property
    def full_name(self):
        return f"{self.name.root}:{self.version.root}"

    @property
    def pk_1(self) -> DynamoDbStringType:
        return DynamoDbStringType(root=DbPrefix.Contract.value)

    @property
    def sk_1(self) -> DynamoDbStringType:
        return DynamoDbStringType(root=f"{self.pk.root}{KEY_SEPARATOR}{self.sk.root}")

    def dict(self, **kwargs):
        return {
            "pk": self.pk.dict(),
            "sk": self.sk.dict(),
            "pk_1": self.pk_1.dict(),
            "sk_1": self.sk_1.dict(),
            **super().dict(**kwargs),
        }
