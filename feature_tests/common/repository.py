from typing import Generator

from pydantic import BaseModel

from nrlf.core.errors import ItemNotFound
from nrlf.core.repository import Repository

CHUNK_SIZE = 25


def _chunk_list(list_a, chunk_size=CHUNK_SIZE):
    for i in range(0, len(list_a), chunk_size):
        yield list_a[i : i + chunk_size]


class FeatureTestRepository(Repository):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delete_all()

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

    def delete_all(self):
        transact_items = [
            {
                "Delete": {
                    "TableName": self.table_name,
                    "Key": {"pk": item["pk"], "sk": item["sk"]},
                }
            }
            for item in self._scan()
        ]
        for chunk in _chunk_list(transact_items):
            self.dynamodb.transact_write_items(TransactItems=chunk)

    def exists(self, pk) -> tuple[BaseModel, bool, str]:
        item = None
        try:
            item = self.read_item(pk)
            exists = True
            message = f"Item found {item.pk}"
        except ItemNotFound as e:
            exists = False
            message = str(e)

        return item, exists, message
