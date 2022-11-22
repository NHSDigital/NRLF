import re
from functools import wraps
from typing import TypeVar

from botocore.exceptions import ClientError
from nrlf.core.dynamodb_types import to_dynamodb_dict
from nrlf.core.errors import DynamoDbError, ItemNotFound, TooManyItemsError
from nrlf.core.model import assert_model_has_only_dynamodb_types
from nrlf.core.types import DynamoDbClient, DynamoDbResponse
from pydantic import BaseModel

PydanticModel = TypeVar("PydanticModel", bound=BaseModel)

MAX_TRANSACT_ITEMS = 100
KEBAB_CASE_RE = re.compile(r"(?<!^)(?=[A-Z])")
ATTRIBUTE_EXISTS_ID = "attribute_exists(id)"
ATTRIBUTE_NOT_EXISTS_ID = "attribute_not_exists(id)"
CONDITION_CHECK_CODES = [
    "ConditionalCheckFailedException",
    "TransactionCanceledException",
    "ValidationException",
]


def to_kebab_case(name: str) -> str:
    return KEBAB_CASE_RE.sub("-", name).lower()


def _handle_dynamodb_errors(function, conditional_check_error_message: str = ""):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ClientError as error:
            if error.response["Error"]["Code"] in CONDITION_CHECK_CODES:
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
        item_type: type[PydanticModel],
        client: DynamoDbClient,
        environment_prefix: str = "",
    ):
        self.dynamodb = client
        self.item_type = item_type
        self.table_name = environment_prefix + to_kebab_case(item_type.__name__)
        assert_model_has_only_dynamodb_types(model=item_type)

    @handle_dynamodb_errors(conditional_check_error_message="Duplicate rejected")
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
            raise ItemNotFound("Item could not be found")
        return self.item_type(**item)

    @handle_dynamodb_errors()
    def search(
        self,
        index_name: str,
        required_page: int = 0,
        current_page: int = 0,
        **kwargs: dict[str, str],
    ) -> list[PydanticModel]:
        global results
        results = self.dynamodb.query(
            TableName=self.table_name, IndexName=index_name, **kwargs
        )
        if current_page != required_page:
            if "LastEvaluatedKey" in results:
                kwargs["ExclusiveStartKey"] = results["LastEvaluatedKey"]
                self.search(
                    index_name=index_name,
                    required_page=required_page,
                    current_page=current_page + 1,
                    **kwargs,
                )

        return [self.item_type(**item) for item in results["Items"]]

    @handle_dynamodb_errors(conditional_check_error_message="Permission denied")
    def update(self, **kwargs: dict[str, str]) -> DynamoDbResponse:
        return self.dynamodb.update_item(TableName=self.table_name, **kwargs)

    @handle_dynamodb_errors(conditional_check_error_message="Supersede ID mismatch")
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
