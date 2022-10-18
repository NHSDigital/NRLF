from ast import literal_eval
from typing import Any, Generic, TypeVar, Union

from pydantic import validator
from pydantic.generics import GenericModel

PythonType = TypeVar("PythonType")
NoneType = type(None)
DYNAMODB_TYPE_LOOKUP = {
    str: "S",
    int: "N",
    float: "N",
    dict: "M",
    list: "L",
    NoneType: "NULL",
}


class DynamoDbType(GenericModel, Generic[PythonType]):
    value: dict[str, Any]

    @property
    def raw_value(self):
        (_raw_value,) = self.value.values()
        return _raw_value

    @validator("value", pre=True)
    def convert_to_dynamodb_format(value):
        return convert_value_to_dynamo_format(value)

    def dict(self, *args, **kwargs):
        return self.value


def convert_value_to_dynamo_format(obj):
    _type = type(obj)

    if _type is dict:
        return {"M": {k: convert_value_to_dynamo_format(v) for k, v in obj.items()}}
    elif _type is list:
        return {"L": [convert_value_to_dynamo_format(item) for item in obj]}
    elif obj is None:
        return {"NULL": True}

    dynamodb_type = DYNAMODB_TYPE_LOOKUP.get(_type)
    return {dynamodb_type: str(obj)}


def convert_dynamo_value_to_raw_value(obj: Union[DynamoDbType, dict]):
    _type = type(obj)

    if _type in (list, dict):
        ((dynamo_type, value),) = obj.items()
    else:
        ((dynamo_type, value),) = obj.value.items()

    if dynamo_type in (DYNAMODB_TYPE_LOOKUP[dict], dict):
        return {k: convert_dynamo_value_to_raw_value(v) for k, v in value.items()}
    elif dynamo_type in (DYNAMODB_TYPE_LOOKUP[list], list):
        return [convert_dynamo_value_to_raw_value(item) for item in value]
    elif dynamo_type in (DYNAMODB_TYPE_LOOKUP[NoneType], NoneType):
        return None

    return literal_eval(value) if dynamo_type == "N" else value


DYNAMODB_NULL = DynamoDbType[NoneType](value=None)
