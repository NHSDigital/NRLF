from functools import partial
from types import FunctionType
from typing import Generator

from nrlf.core_pipeline.repository import Repository
from nrlf.core_pipeline.types import DynamoDBClient

CHUNK_SIZE = 25


def _chunk_list(list_a, chunk_size=CHUNK_SIZE):
    for i in range(0, len(list_a), chunk_size):
        yield list_a[i : i + chunk_size]


class SandboxRepository(Repository):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._delete_all()

    def _scan(self) -> Generator[dict, None, None]:
        items = []
        start_key_kwargs = {}
        while True:
            response = self.dynamodb.scan(TableName=self.table_name, **start_key_kwargs)
            yield from response["Items"]
            try:
                start_key_kwargs = {"ExclusiveStartKey": response["LastEvaluatedKey"]}
            except KeyError:
                break

        return items

    def _delete_all(self):
        transact_items = [
            {
                "Delete": {
                    "TableName": self.table_name,
                    "Key": self._get_key(item=item),
                }
            }
            for item in self._scan()
        ]
        for chunk in _chunk_list(transact_items):
            self.dynamodb.transact_write_items(TransactItems=chunk)

    def _get_key(self, item):
        key_schema = None
        if self.table_name == "dummy-model":
            key_schema = {"id": item["id"]}
        else:
            key_schema = {"pk": item["pk"], "sk": item["sk"]}
        return key_schema

    def create_all(self, items: list):
        transact_items = [
            {
                "Put": {
                    "TableName": self.table_name,
                    "Item": item.dict(),
                }
            }
            for item in items
        ]
        for chunk in _chunk_list(transact_items):
            self.dynamodb.transact_write_items(TransactItems=chunk)

    @classmethod
    def factory(cls, client: DynamoDBClient, environment_prefix: str) -> FunctionType:
        return partial(cls, client=client, environment_prefix=environment_prefix)
