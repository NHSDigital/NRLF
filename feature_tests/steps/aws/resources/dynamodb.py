from nrlf.core.model import DocumentPointer
from nrlf.core.repository import Repository
from nrlf.core.types import DynamoDbClient
from pydantic import BaseModel

from feature_tests.steps.aws.resources.common import get_terraform_json


def _chunk_list(list_a, chunk_size):
    for i in range(0, len(list_a), chunk_size):
        yield list_a[i : i + chunk_size]


class FeatureTestDynamoRepository(Repository):
    def __init__(
        self,
        item_type: type[BaseModel],
        client: DynamoDbClient,
        keys: list[str],
        environment_prefix: str = "",
    ):
        super().__init__(item_type, client, environment_prefix)
        self.keys = keys

    def _scan(self) -> list:
        items = []
        response = self.dynamodb.scan(TableName=self.table_name)
        items += response["Items"]
        start_key = response.get("LastEvaluatedKey", None)
        while start_key:
            response = self.dynamodb.scan(TableName=self.table_name)
            items += response["Items"]
            start_key = response.get("LastEvaluatedKey", None)

        return items

    def _transact_write(self, items: list):
        if len(items) > 0:
            for chunk in _chunk_list(items, 25):
                self.dynamodb.transact_write_items(TransactItems=chunk)

    def delete_all(self):
        print(f"cleaning table {self.table_name}")
        all_items = self._scan()
        transact_items = []
        for item in all_items:
            param = {"Delete": {"TableName": self.table_name, "Key": {}}}
            for key in self.keys:
                param["Delete"]["Key"][key] = item[key]
            transact_items.append(param)
        self._transact_write(transact_items)


class FeatureTestDocumentPointerRepository(FeatureTestDynamoRepository):
    def __init__(self, client: DynamoDbClient, environmental_prefix: str = ""):
        super().__init__(DocumentPointer, client, ["id"], environmental_prefix)


_DYNAMO_DB_REPOSITORY_MAP = {"Document Pointers": FeatureTestDocumentPointerRepository}


def get_dynamo_db_repository(context, table_name: str):
    if context.local_test:
        return _DYNAMO_DB_REPOSITORY_MAP[table_name](client=context.dynamodb_client)

    return _DYNAMO_DB_REPOSITORY_MAP[table_name](
        client=context.dynamodb_client,
        environmental_prefix=f'{get_terraform_json()["prefix"]["value"]}--',
    )
