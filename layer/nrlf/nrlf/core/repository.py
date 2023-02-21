import json
import re
from functools import reduce, wraps
from typing import Optional, TypeVar, Union

from botocore.exceptions import ClientError
from lambda_utils.logging import log_action
from more_itertools import map_except
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
from pydantic import BaseModel, ValidationError

from .decorators import deprecated

PydanticModel = TypeVar("PydanticModel", bound=BaseModel)

MAX_TRANSACT_ITEMS = 100
MAX_RESULTS = 100
ATTRIBUTE_EXISTS_PK = "attribute_exists(pk)"
ATTRIBUTE_NOT_EXISTS_PK = "attribute_not_exists(pk)"
CONDITION_CHECK_CODES = [
    "ConditionalCheckFailedException",
    "TransactionCanceledException",
    "ValidationException",
]


def _strip_none(d: dict) -> dict:
    if d is None:
        return None
    return {k: v for (k, v) in d.items() if f"{v}" != "None"}


def _validate_results_within_limits(results: dict):
    if len(results["Items"]) >= MAX_RESULTS or "LastEvaluatedKey" in results:
        raise Exception(
            "DynamoDB has returned too many results, pagination not implemented yet"
        )
    return results


def _valid_results(item_type: type[DynamoDbModel], results: dict):
    """
    returns only valid results for the specified type[DynamoDbModel]
    """
    valid_results = []
    for item in results:
        try:
            valid_results.append(item_type(**item))
        except (ValueError, ValidationError) as e:
            pass

    return valid_results


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


def _keys(pk, sk, pk_name="pk", sk_name="sk"):
    keys = {pk_name: {"S": f"{pk}"}}
    if f"{sk}" != "None":
        keys[sk_name] = {"S": f"{sk}"}
    return keys


NoneType = type(None)
DYNAMODB_ENCODE_LOOKUP = {
    bool: "B",
    str: "S",
    int: "N",
    float: "N",
    dict: "M",
    list: "L",
    NoneType: "NULL",
}


def _encode(v: any) -> dict:
    """
    encodes a value into dynamodb object

    e.g. 123 -> { "N": 123 }
    """
    k = DYNAMODB_ENCODE_LOOKUP.get(type(v))
    if k == "NULL":
        return {"NULL": True}
    if k == "M":
        return {"M": {kk: _encode(vv) for (kk, vv) in v.items()}}
    return {k: v}


def _decode_dict(node: dict[str, any]) -> dict[str, any]:
    """
    recursively decodes a dynamodb map
    """
    return {k: _decode(v) for (k, v) in node["M"].items()}


def _decode_list(node) -> list[any]:
    """
    recursively decodes a dynamodb list
    """
    return [_decode(v) for v in node["L"]]


def _decode_number(node) -> Union[int, float]:
    """
    Tries to maintain integer precision by guessing
    """
    f = float(node["N"])
    i = int(f)
    return i if i == f else f


DYNAMODB_DECODE_LOOKUP = {
    "NULL": lambda node: None,
    "B": lambda node: bool(node["B"]),
    "S": lambda node: str(node["S"]),
    "N": _decode_number,
    "M": _decode_dict,
    "L": _decode_list,
}


def _decode(node: dict) -> any:
    """
    decodes a dynamodb object into a value

    e.g. {"N":123} -> 123
    """
    key = "".join(node.keys()).upper()
    fn = DYNAMODB_DECODE_LOOKUP[key]
    if fn:
        return fn(node)
    raise Exception(f"Unhandled DynamoDb type: {key}")


def _key_condition_expression(d: dict) -> str:
    """
    Used to generate the 'KeyConditionExpression' parameter in dynamodb queries.
    It delivers a simpler interface by reducing the number of operators to
    'AND', '=' and 'in' as those are the only ones we use.

    { "foo": 123, "bar": "green" } -> "foo = :foo" AND bar = :bar"
    """
    return " AND ".join([f"{k} = :{k}" for (k, v) in d.items() if f"{v}" != "None"])


def _filter_expression(d: dict) -> str:
    """
    Used to generate the 'FilterExpression' parameter in dynamodb queries.  It
    delivers a simpler interface by reducing the the number of operators to
    'AND', '=' and 'in' as those are the only ones we use.

    { "foo": 123, "bar": "green" } -> "#foo = :foo AND #bar = :bar"
    """

    def _item(key: str, value: any) -> str:
        if type(value) == list:
            items = ", ".join([f":{key}_{ix}" for ix in range(1, len(value) + 1)])
            return f"#{key} in ({items})"
        return f"#{key} = :{key}"

    return " AND ".join([_item(k, v) for (k, v) in d.items()])


def _expression_attribute_names(d: dict) -> dict:
    """
    Used to generate the 'ExpressionAttributeNames' parameter in dynamodb
    queries.

    { "foo": "123", "bar": "green" } -> { "#foo": "foo", "#bar": "bar" }
    """
    return {f"#{k}": k for k in d}


def _expression_attribute_values(d: dict) -> dict:
    """
    Used to generate the 'ExpressionAttributeValues' parameter in dynamodb
    queries.

    { "foo": 123, "bar": "green" } -> { ":foo": 123, ":bar": "green" }
    """

    def _item(key: str, value: any) -> str:
        if type(value) == list:
            return {f":{key}_{ix+1}": _encode(value[ix]) for ix in range(len(value))}
        return {f":{key}": _encode(value)}

    return reduce(
        lambda a, b: ({**a, **b}),
        [_item(k, v) for (k, v) in d.items()],
        {},
    )


def _key_and_filter_clause(keys: dict, filter: dict = None):
    keys = _strip_none(keys)
    filter = _strip_none(filter)
    if filter is None or filter == {}:
        return {
            "KeyConditionExpression": _key_condition_expression(keys),
            "ExpressionAttributeValues": _expression_attribute_values(keys),
        }
    else:
        return {
            "KeyConditionExpression": _key_condition_expression(keys),
            "FilterExpression": _filter_expression(filter),
            "ExpressionAttributeNames": _expression_attribute_names(filter),
            "ExpressionAttributeValues": {
                **_expression_attribute_values(keys),
                **_expression_attribute_values(filter),
            },
        }


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
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
        )

    @deprecated("Use `get` instead.")
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
    def read_item(
        self,
        pk,
        sk=None,
        **filter,
    ) -> PydanticModel:
        """
        Returns a single record from the database
        """
        clause = _key_and_filter_clause({"pk": f"{pk}", "sk": f"{sk or pk}"}, filter)
        response = self.dynamodb.query(
            TableName=self.table_name,
            **clause,
        )
        try:
            (item,) = response["Items"]
        except (KeyError, ValueError):
            raise ItemNotFound("Item could not be found") from None
        return self.item_type(**item)

    @handle_dynamodb_errors()
    @log_action(
        narrative="Querying document",
        log_fields=["pk", "sk_name", "index_name", "pk_name", "sk"],
    )
    def _query(
        self,
        index_name,
        pk_name: str,
        pk: str,
        sk_name: str = None,
        sk: str = None,
        **filter,
    ) -> list[PydanticModel]:
        """
        Do not call this method directly, instead use `query` or `query_gsi_#` instead.
        """
        clause = _key_and_filter_clause(
            {pk_name: f"{pk}"} if sk is None else {pk_name: f"{pk}", sk_name: f"{sk}"},
            filter,
        )

        args = _strip_none(
            {"TableName": self.table_name, "IndexName": index_name, **clause}
        )
        results = self.dynamodb.query(**args)
        _validate_results_within_limits(results)
        valid_results = _valid_results(self.item_type, results["Items"])
        return valid_results

    def query(
        self,
        pk,
        sk=None,
        **filter,
    ) -> list[PydanticModel]:
        """
        Query records using the main partition key
        """
        return self._query(None, "pk", pk, "sk", sk, **filter)

    def query_gsi_1(
        self,
        pk,
        sk=None,
        **filter,
    ) -> list[PydanticModel]:
        """
        Query records using the Global Secondary Index 'idx_gsi_1'
        """
        return self._query("idx_gsi_1", "pk_1", pk, "sk_1", sk, **filter)

    def query_gsi_2(
        self,
        pk,
        sk=None,
        **filter,
    ) -> list[PydanticModel]:
        """
        Query records using the Global Secondary Index 'idx_gsi_2'
        """
        return self._query("idx_gsi_2", "pk_2", pk, "sk_2", sk, **filter)

    def query_gsi_3(
        self,
        pk,
        sk=None,
        **filter,
    ) -> list[PydanticModel]:
        """
        Query records using the Global Secondary Index 'idx_gsi_3'
        """
        return self._query("idx_gsi_3", "pk_3", pk, "sk_3", sk, **filter)

    def query_gsi_4(
        self,
        pk,
        sk=None,
        **filter,
    ) -> list[PydanticModel]:
        """
        Query records using the Global Secondary Index 'idx_gsi_4'
        """
        return self._query("idx_gsi_4", "pk_4", pk, "sk_4", sk, **filter)

    def query_gsi_5(
        self,
        pk,
        sk=None,
        **filter,
    ) -> list[PydanticModel]:
        """
        Query records using the index 'idx_gsi_5'
        """
        return self._query("idx_gsi_5", "pk_5", pk, "sk_5", sk, **filter)

    @handle_dynamodb_errors(conditional_check_error_message="Permission denied")
    def update(self, item: PydanticModel) -> DynamoDbResponse:
        """
        Update a single Record
        """
        args = {
            "TableName": self.table_name,
            "Item": item.dict(),
            "ConditionExpression": "attribute_exists(pk) AND attribute_exists(sk)",
        }
        return self.dynamodb.put_item(**args)

    @handle_dynamodb_errors(
        conditional_check_error_message="Supersede ID mismatch",
        error_type=SupersedeError,
    )
    def supersede(
        self, create_item: PydanticModel, delete_pks: list[str]
    ) -> DynamoDbResponse:
        """
        Creates a new Record and delete existing records in a single transaction
        """

        def _put():
            return {
                "Put": {
                    "TableName": self.table_name,
                    "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                    "Item": create_item.dict(),
                }
            }

        def _delete(id):
            return {
                "Delete": {
                    "TableName": self.table_name,
                    "ConditionExpression": "attribute_exists(pk) AND attribute_exists(sk)",
                    "Key": _keys(id, id),
                }
            }

        if len(delete_pks) >= MAX_TRANSACT_ITEMS:
            raise TooManyItemsError("Too many items to process in one transaction")
        transact_items = [_delete(id) for id in delete_pks] + [_put()]
        return self.dynamodb.transact_write_items(TransactItems=transact_items)

    @handle_dynamodb_errors(conditional_check_error_message="Forbidden")
    def hard_delete(self, pk, sk=None) -> DynamoDbResponse:
        keys = _keys(
            pk, sk or pk
        )  # if no SK then the table uses same value of SK as PK.
        args = {
            "TableName": self.table_name,
            "Key": keys,
            "ConditionExpression": "attribute_exists(pk) AND attribute_exists(sk)",
        }
        self.dynamodb.delete_item(**args)
