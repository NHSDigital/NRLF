import json

from nrlf.core_pipeline.dynamodb_types import DynamoDbStringType
from nrlf.core_pipeline.model import DynamoDbModel
from nrlf.core_pipeline.types import DynamoDBClient


class DummyModel(DynamoDbModel):
    id: DynamoDbStringType


def create_table(client: DynamoDBClient, item_type_name: str):
    client.create_table(
        TableName=item_type_name,
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
    )


def create_dummy_model_json_file(
    raw_data: list[dict], template_path_to_data: str, item_type_name: str
):
    with open(template_path_to_data.format(item_type_name=item_type_name), "w") as f:
        f.write(json.dumps(raw_data))
