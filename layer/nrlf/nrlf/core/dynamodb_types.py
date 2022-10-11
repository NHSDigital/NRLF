import json
from typing import Generic, TypeVar
from pydantic import validator
from pydantic.generics import GenericModel

PythonType = TypeVar("PythonType")
DYNAMODB_TYPE_LOOKUP = {str: "S", int: "N", float: "N"}


class DynamoDbType(GenericModel, Generic[PythonType]):
    value: dict[str, PythonType]

    @property
    def raw_value(self):
        (_raw_value,) = self.value.values()
        return _raw_value

    @validator("value", pre=True)
    def convert_to_dynamodb_format(value):
        dynamodb_type = DYNAMODB_TYPE_LOOKUP.get(type(value))
        if dynamodb_type:
            return {dynamodb_type: value}
        return value

    def dict(self, *args, **kwargs):
        return self.value

    def json(self, *args, **kwargs):
        return json.dumps(self.dict(*args, **kwargs))
