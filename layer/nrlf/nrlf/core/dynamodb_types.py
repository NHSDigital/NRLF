from ast import literal_eval
from typing import Any, TypeVar, Union

from pydantic import Field, RootModel, StrictInt, StrictStr, model_serializer

PythonType = TypeVar("PythonType")
NoneType = type(None)
DYNAMODB_TYPE_LOOKUP = {
    str: "S",
    int: "N",
    float: "N",
    dict: "M",
    list: "L",
    bool: "BOOL",
    NoneType: "NULL",
}


class DynamoDbType(RootModel):
    @model_serializer()
    def serialize_to_dynamodb(self, *args, **kwargs):
        return convert_value_to_dynamo_format(self.root)

    @property
    def value(self):
        return self.root

    def __str__(self):
        return f"{self.root}"


class DynamoDbStringType(DynamoDbType):
    root: StrictStr


class DynamoDbIntType(DynamoDbType):
    root: StrictInt


class DynamoDbNullType(DynamoDbType):
    root: None = None


class DynamoDbListType(DynamoDbType):
    root: list[str] = Field(default_factory=list)


class DynamoDbDictType(DynamoDbType):
    root: dict


def convert_value_to_dynamo_format(obj):
    _type = type(obj)

    if _type is dict:
        return {"M": {k: convert_value_to_dynamo_format(v) for k, v in obj.items()}}
    elif _type is list:
        return {"L": [convert_value_to_dynamo_format(item) for item in obj]}
    elif _type is bool:
        return {"BOOL": obj}
    elif _type is NoneType:
        return {"NULL": True}

    dynamodb_type = DYNAMODB_TYPE_LOOKUP.get(_type)
    return {dynamodb_type: str(obj)}


def convert_dynamo_value_to_raw_value(obj: Union[DynamoDbType, dict]):
    _type = type(obj)
    if _type in (list, dict):
        ((dynamo_type, value),) = obj.items()
    else:
        ((dynamo_type, value),) = obj.model_dump().items()

    if dynamo_type in (DYNAMODB_TYPE_LOOKUP[dict], dict):
        return {k: convert_dynamo_value_to_raw_value(v) for k, v in value.items()}
    elif dynamo_type in (DYNAMODB_TYPE_LOOKUP[list], list):
        return [convert_dynamo_value_to_raw_value(item) for item in value]
    elif dynamo_type in (DYNAMODB_TYPE_LOOKUP[NoneType], NoneType):
        return None

    return literal_eval(value) if dynamo_type == "N" else value


def is_dynamodb_dict(obj: Any) -> bool:
    try:
        convert_dynamo_value_to_raw_value(obj)
    except:
        return False
    return True


DYNAMODB_NULL = DynamoDbNullType()
DYNAMODBTYPE_TYPE_LOOKUP = {
    str: DynamoDbStringType,
    int: DynamoDbIntType,
    NoneType: DynamoDbNullType,
    list: DynamoDbListType,
}


def to_dynamodb_dict(value: PythonType) -> dict[str, PythonType]:
    return DYNAMODBTYPE_TYPE_LOOKUP[type(value)](root=value).dict()
