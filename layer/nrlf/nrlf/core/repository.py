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

    def read(self, key: any):
        return self.dynamodb.get_item(TableName=self.table_name, Key={"id": key})

    def search(self, key: any):
        return self.dynamodb.get_item(Key={key})

    def update(self):
        pass

    def supersede(self, item: BaseModel):
        pass

    def soft_delete(self):
        pass

    def hard_delete(self):
        pass
