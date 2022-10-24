import re

import boto3
from nrlf.core.dynamodb_types import DynamoDbType
from nrlf.core.validators import make_timestamp
from pydantic import BaseModel


def _to_snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


class Repository:
    def __init__(self, item_type: BaseModel, client):
        self.dynamodb = client
        self.item_type = item_type
        self.table_name = _to_snake_case(item_type.__name__)
        for key, value in item_type.__fields__.items():
            if not issubclass(value.type_, DynamoDbType):
                print(key, value.type_)
                raise TypeError(
                    "Model contains fields that are not of type DynamoDbType"
                )

    def create(self, item: BaseModel):
        return self.dynamodb.put_item(TableName=self.table_name, Item=item)

    def read(self, **kwargs):
        response = self.dynamodb.get_item(TableName=self.table_name, Key=kwargs)
        return self.item_type.construct(**response["Item"])

    def search(self, key: any):
        return NotImplementedError

    def update(self, item: BaseModel):
        return self.dynamodb.put_item(TableName=self.table_name, Item=item)

    def supersede(self, item: BaseModel):
        return NotImplementedError

    def soft_delete_document_pointer(self, id: str, status=None):
        update_expression = "SET deleted_on = :now"
        expression_attribute = {":now": {"S": make_timestamp()}}

        if status is not None:
            updateExpression += ", status = :status"
            expression_attribute[":status"] = {"S": status}

        return self.dynamodb.update_item(
            Key={"id": id},
            TableName="document-pointer",
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute,
        )

    def hard_delete(self, id: str):
        return self.dynamodb.delete_item(TableName=self.table_name, Key={"id": id})
