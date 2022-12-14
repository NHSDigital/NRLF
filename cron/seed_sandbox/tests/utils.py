import json

from nrlf.core.dynamodb_types import (
    DynamoDbStringType,
    convert_dynamo_value_to_raw_value,
    is_dynamodb_dict,
)
from nrlf.core.types import DynamoDbClient
from pydantic import BaseModel, Field, root_validator


class DummyModel(BaseModel):
    id: DynamoDbStringType
    _from_dynamo: bool = Field(
        default=False,
        exclude=True,
        description="internal flag for reading from dynamodb",
    )

    @root_validator(pre=True)
    def transform_input_values_if_dynamo_values(cls, values: dict) -> dict:
        from_dynamo = all(map(is_dynamodb_dict, values.values()))

        if from_dynamo:
            return {
                **{k: convert_dynamo_value_to_raw_value(v) for k, v in values.items()},
                "_from_dynamo": from_dynamo,
            }
        return values


def create_table(client: DynamoDbClient, item_type_name: str):
    client.create_table(
        TableName=item_type_name,
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )


def create_local_raw_data(
    raw_data: list[dict], template_path_to_data: str, item_type_name: str
):
    with open(template_path_to_data.format(item_type_name=item_type_name), "w") as f:
        f.write(json.dumps(raw_data))


def sort_models(models: list[DummyModel]) -> list[DummyModel]:
    return sorted(models, key=lambda model: model.id.__root__)
