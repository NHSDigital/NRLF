import re

import boto3
from nrlf.core.dynamodb_types import DynamoDbType
from nrlf.core.validators import make_timestamp
from pydantic import BaseModel
from boto3.dynamodb.conditions import Attr


def _to_kebab_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


class DynamoDbResponse(dict):
    pass


class Repository:
    def __init__(self, item_type: BaseModel, client):
        self.dynamodb = client
        self.item_type = item_type
        self.table_name = _to_kebab_case(item_type.__name__)
        for key, value in item_type.__fields__.items():
            if not issubclass(value.type_, DynamoDbType):
                raise TypeError(
                    "Model contains fields that are not of type DynamoDbType"
                )

    def create(self, item: BaseModel) -> DynamoDbResponse:
        return self.dynamodb.put_item(TableName=self.table_name, Item=item.dict())

    def read(self, **kwargs) -> DynamoDbResponse:
        response = self.dynamodb.get_item(TableName=self.table_name, Key=kwargs)
        if "Item" in response:
            return self.item_type.construct(**response["Item"])

    def search(self, key: any):
        return NotImplementedError

    def update(self, item: BaseModel) -> DynamoDbResponse:
        return self.dynamodb.put_item(TableName=self.table_name, Item=item)

    def supersede(
        self, create_item: BaseModel, delete_item_id: str
    ) -> DynamoDbResponse:
        return self.dynamodb.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "TableName": self.table_name,
                        "ConditionExpression": "attribute_not_exists(id)",
                        "Item": create_item.dict(),
                    }
                },
                {
                    "Delete": {
                        "TableName": self.table_name,
                        "Key": {"id": delete_item_id},
                    }
                },
            ]
        )

    def hard_delete(self, id: str):
        return self.dynamodb.delete_item(TableName=self.table_name, Key={"id": id})
