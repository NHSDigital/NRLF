import re
from functools import wraps
from typing import TypeVar

from botocore.exceptions import ClientError
from nrlf.core.dynamodb_types import to_dynamodb_dict
from nrlf.core.errors import (
    DuplicateError,
    DynamoDbError,
    ItemNotFound,
    SupersedeError,
    TooManyItemsError,
)
from nrlf.core.model import DynamoDbModel
from nrlf.core.types import DynamoDbClient, DynamoDbResponse
from pydantic import BaseModel

PydanticModel = TypeVar("PydanticModel", bound=BaseModel)

MAX_TRANSACT_ITEMS = 100
MAX_RESULTS = 100
ATTRIBUTE_EXISTS_ID = "attribute_exists(id)"
ATTRIBUTE_NOT_EXISTS_ID = "attribute_not_exists(id)"
CONDITION_CHECK_CODES = [
    "ConditionalCheckFailedException",
    "TransactionCanceledException",
    "ValidationException",
]


def _validate_results_within_limits(results: dict):
    if len(results["Items"]) >= MAX_RESULTS or "LastEvaluatedKey" in results:
        raise Exception(
            "DynamoDB has returned too many results, pagination not implemented yet"
        )
    return results


def _handle_dynamodb_errors(
    function, conditional_check_error_message: str = "", error_type=DynamoDbError
):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ClientError as error:
            error_code = error.response["Error"]["Code"]
            if error_code in CONDITION_CHECK_CODES:
                raise error_type(
                    f"Condition check failed - {conditional_check_error_message or error_code}"
                )
            raise Exception(f"There was an error with the database: {error}")

    return wrapper


def handle_dynamodb_errors(
    conditional_check_error_message: str = "", error_type=DynamoDbError
):
    return lambda function: _handle_dynamodb_errors(
        function,
        conditional_check_error_message=conditional_check_error_message,
        error_type=error_type,
    )


class Repository:
    def __init__(
        self,
        item_type: type[DynamoDbModel],
        client: DynamoDbClient,
        environment_prefix: str = "",
    ):
        self.dynamodb = client
        self.item_type = item_type
        self.table_name = environment_prefix + item_type.kebab()

    @handle_dynamodb_errors(
        conditional_check_error_message="Duplicate item", error_type=DuplicateError
    )
    def create(self, item: PydanticModel) -> DynamoDbResponse:
        return self.dynamodb.put_item(
            TableName=self.table_name,
            Item=item.dict(),
            ConditionExpression=ATTRIBUTE_NOT_EXISTS_ID,
        )

    @handle_dynamodb_errors()
    def read(self, KeyConditionExpression: str, **kwargs) -> PydanticModel:
        response = self.dynamodb.query(
            TableName=self.table_name,
            KeyConditionExpression=KeyConditionExpression,
            **kwargs,
        )
        try:
            (item,) = response["Items"]
        except (KeyError, ValueError):
            raise ItemNotFound("Item could not be found") from None
        return self.item_type(**item)

    @handle_dynamodb_errors()
    def search(
        self,
        index_name: str,
        **kwargs: dict[str, str],
    ) -> list[PydanticModel]:
        results = self.dynamodb.query(
            TableName=self.table_name, IndexName=index_name, **kwargs
        )
        _validate_results_within_limits(results)
        return [self.item_type(**item) for item in results["Items"]]

    @handle_dynamodb_errors(conditional_check_error_message="Permission denied")
    def update(self, **kwargs: dict[str, str]) -> DynamoDbResponse:
        return self.dynamodb.update_item(TableName=self.table_name, **kwargs)

    @handle_dynamodb_errors(
        conditional_check_error_message="Supersede ID mismatch",
        error_type=SupersedeError,
    )
    def supersede(
        self, create_item: PydanticModel, delete_item_ids: list[str]
    ) -> DynamoDbResponse:
        if len(delete_item_ids) >= MAX_TRANSACT_ITEMS:
            raise TooManyItemsError("Too many items to process in one transaction")

        transact_items = [
            {
                "Delete": {
                    "TableName": self.table_name,
                    "ConditionExpression": ATTRIBUTE_EXISTS_ID,
                    "Key": {"id": to_dynamodb_dict(id)},
                }
            }
            for id in delete_item_ids
        ] + [
            {
                "Put": {
                    "TableName": self.table_name,
                    "ConditionExpression": ATTRIBUTE_NOT_EXISTS_ID,
                    "Item": create_item.dict(),
                }
            }
        ]
        return self.dynamodb.transact_write_items(TransactItems=transact_items)

    @handle_dynamodb_errors(conditional_check_error_message="Forbidden")
    def hard_delete(self, **kwargs: dict[str, str]) -> DynamoDbResponse:
        self.dynamodb.delete_item(TableName=self.table_name, **kwargs)
