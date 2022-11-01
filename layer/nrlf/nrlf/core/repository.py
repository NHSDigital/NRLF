import re
from functools import wraps

from botocore.exceptions import ClientError
from nrlf.core.errors import DynamoDbError, ItemNotFound
from nrlf.core.model import assert_model_has_only_dynamodb_types
from nrlf.core.types import DynamoDbClient, DynamoDbResponse
from pydantic import BaseModel

MAX_RESULTS = 100
CAMEL_CASE_RE = re.compile(r"(?<!^)(?=[A-Z])")
ATTRIBUTE_EXISTS_ID = "attribute_exists(id)"
ATTRIBUTE_NOT_EXISTS_ID = "attribute_not_exists(id)"


def _to_kebab_case(name: str) -> str:
    return CAMEL_CASE_RE.sub("-", name).lower()


def _validate_results_within_limits(results: dict):
    if len(results["Items"]) >= MAX_RESULTS or "LastEvaluatedKey" in results:
        raise Exception(
            "DynamoDB has returned too many results, pagination not implemented yet"
        )
    return results


def _handle_dynamodb_errors(function, conditional_check_error_message: str = ""):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ClientError as error:
            if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise DynamoDbError(
                    f"Condition check failed - {conditional_check_error_message}"
                )
            raise Exception("There was an error with the database")

    return wrapper


def handle_dynamodb_errors(conditional_check_error_message: str = ""):
    return lambda function: _handle_dynamodb_errors(
        function, conditional_check_error_message
    )


class Repository:
    def __init__(
        self,
        item_type: type[BaseModel],
        client: DynamoDbClient,
        environment_prefix: str = "",
    ):
        self.dynamodb = client
        self.item_type = item_type
        self.table_name = environment_prefix + _to_kebab_case(item_type.__name__)
        assert_model_has_only_dynamodb_types(model=item_type)

    @handle_dynamodb_errors(conditional_check_error_message="Duplicate rejected")
    def create(self, item: BaseModel) -> DynamoDbResponse:
        return self.dynamodb.put_item(
            TableName=self.table_name,
            Item=item.dict(),
            ConditionExpression=ATTRIBUTE_NOT_EXISTS_ID,
        )

    @handle_dynamodb_errors()
    def read(self, KeyConditionExpression: str, **kwargs) -> BaseModel:
        response = self.dynamodb.query(
            TableName=self.table_name,
            KeyConditionExpression=KeyConditionExpression,
            **kwargs,
        )
        try:
            (item,) = response["Items"]
        except (KeyError, ValueError):
            raise ItemNotFound
        return self.item_type(**item)

    @handle_dynamodb_errors()
    def search(self, index_name: str, **kwargs: dict[str, str]) -> list[BaseModel]:
        results = self.dynamodb.query(
            TableName=self.table_name, IndexName=index_name, **kwargs
        )
        _validate_results_within_limits(results)
        return [self.item_type.construct(**item) for item in results["Items"]]

    @handle_dynamodb_errors(conditional_check_error_message="Document does not exist")
    def update(self, item: BaseModel) -> DynamoDbResponse:
        return self.dynamodb.put_item(
            TableName=self.table_name,
            Item=item.dict(),
            ConditionExpression=ATTRIBUTE_EXISTS_ID,
        )

    @handle_dynamodb_errors(conditional_check_error_message="Supersede failed")
    def supersede(
        self, create_item: BaseModel, delete_item_id: dict
    ) -> DynamoDbResponse:
        return self.dynamodb.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "TableName": self.table_name,
                        "ConditionExpression": ATTRIBUTE_NOT_EXISTS_ID,
                        "Item": create_item.dict(),
                    }
                },
                {
                    "Delete": {
                        "TableName": self.table_name,
                        "Key": {"id": delete_item_id},
                        "ConditionExpression": ATTRIBUTE_EXISTS_ID,
                    }
                },
            ]
        )

    @handle_dynamodb_errors(conditional_check_error_message="")
    def hard_delete(self, id: dict) -> DynamoDbResponse:
        return self.dynamodb.delete_item(
            TableName=self.table_name,
            Key={"id": id},
            ConditionExpression=ATTRIBUTE_EXISTS_ID,
        )
