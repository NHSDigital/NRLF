from nrlf.core.validators import make_timestamp
import boto3
from pydantic import BaseModel


class Repository:
    table_name: str
    dynamodb: any

    def __init__(self, table_name: str):
        self.dynamodb = boto3.client("dynamodb")
        self.table_name = table_name

    def create(self, item: BaseModel):
        return self.dynamodb.put_item(TableName=self.table_name, Item=item)

    def read(self, id: str):
        return self.dynamodb.get_item(TableName=self.table_name, Key={"id": id})

    def search(self, key: any):
        return self.dynamodb.get_item(Key={key})

    def update(self, item: BaseModel):
        return self.dynamodb.put_item(TableName=self.table_name, Item=item)

    def supersede(self, item: BaseModel):
        pass

    def soft_delete(self, id: str):

        return self.dynamodb.update_item(
            Key={"id": id},
            TableName=self.table_name,
            UpdateExpression="SET deleted_on = :now",
            ExpressionAttributeValues={":now": {"S": make_timestamp()}},
        )

    def hard_delete(self):
        pass
