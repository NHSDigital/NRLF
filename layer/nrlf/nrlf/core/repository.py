import re
from functools import wraps

from nrlf.core.dynamodb_types import DynamoDbType
from nrlf.core.errors import DynamoDbError, ItemNotFound
from pydantic import BaseModel


def _to_kebab_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


class DynamoDbResponse(dict):
    pass


def handle_dynamodb_errors(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as error:
            if type(error) is ItemNotFound:
                raise error
            raise DynamoDbError("There was an error with the database")

    return wrapper


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

    @handle_dynamodb_errors
    def create(self, item: BaseModel) -> DynamoDbResponse:
        return self.dynamodb.put_item(
            TableName=self.table_name,
            Item=item.dict(),
            ConditionExpression="attribute_not_exists(id)",
        )

    @handle_dynamodb_errors
    def read(self, **kwargs) -> DynamoDbResponse:
        response = self.dynamodb.get_item(TableName=self.table_name, Key=kwargs)

        try:
            item = response["Item"]
        except KeyError:
            raise ItemNotFound("Item could not be found")

        return self.item_type.construct(**item)

    @handle_dynamodb_errors
    def search(self, key: any):
        return NotImplementedError

    @handle_dynamodb_errors
    def update(self, item: BaseModel) -> DynamoDbResponse:
        return self.dynamodb.put_item(
            TableName=self.table_name,
            Item=item.dict(),
            ConditionExpression="attribute_exists(id)",
        )

    @handle_dynamodb_errors
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

    @handle_dynamodb_errors
    def hard_delete(self, id: str):
        return self.dynamodb.delete_item(
            TableName=self.table_name,
            Key={"id": id},
            ConditionExpression="attribute_exists(id)",
        )
