from enum import Enum
from functools import reduce, wraps
from typing import Iterator, TypeVar, Union

from botocore.exceptions import ClientError
from lambda_utils.logging import log_action
from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError

from nrlf.consumer.fhir.r4.model import RequestQueryCustodian
from nrlf.core.errors import (
    DuplicateError,
    DynamoDbError,
    ItemNotFound,
    SupersedeError,
    TooManyItemsError,
)
from nrlf.core.model import DynamoDbModel, PaginatedResponse
from nrlf.core.transform import (
    transform_evaluation_key_to_next_page_token,
    transform_next_page_token_to_start_key,
)
from nrlf.core.types import DynamoDbClient, DynamoDbResponse
from nrlf.producer.fhir.r4.model import RequestQueryType

from .decorators import deprecated

PydanticModel = TypeVar("PydanticModel", bound=BaseModel)

MAX_TRANSACT_ITEMS = 100
PAGE_ITEM_LIMIT = 20
ATTRIBUTE_EXISTS_PK = "attribute_exists(pk)"
ATTRIBUTE_NOT_EXISTS_PK = "attribute_not_exists(pk)"
CONDITION_CHECK_CODES = [
    "ConditionalCheckFailedException",
    "TransactionCanceledException",
    "ValidationException",
]


class LogReference(Enum):
    REPOSITORY001 = "Checking if record is valid"
    REPOSITORY002 = "Querying document"


class CorruptDocumentPointer(Exception):
    pass


def _strip_none(d: dict) -> dict:
    if d is None:
        return None
    return {k: v for (k, v) in d.items() if v is not None}


def custodian_filter(custodian_identifier: RequestQueryCustodian):
    if custodian_identifier is not None:
        return custodian_identifier.__root__.split("|", 1)[1]
    return None


def type_filter(type_identifier: RequestQueryType, pointer_types):
    if type_identifier is not None:
        return [type_identifier.__root__]
    return pointer_types


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


@log_action(log_reference=LogReference.REPOSITORY001, log_fields=["item"])
def _is_record_valid(item_type: type[DynamoDbModel], item: dict):
    try:
        return item_type(**item)
    except (ValueError, ValidationError):
        raise CorruptDocumentPointer(
            f"Document pointer has corrupt data, ignoring ${item}"
        )


def _keys(pk, sk, pk_name="pk", sk_name="sk"):
    keys = {pk_name: {"S": f"{pk}"}}
    if sk is not None:
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
    k = DYNAMODB_ENCODE_LOOKUP[type(v)]
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
    "NULL": lambda _: None,
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


def _key_and_filter_clause(key_conditions: dict, filter: dict = None):
    filter = _strip_none(filter)
    if not filter:
        return {
            "KeyConditionExpression": _key_condition_expression(key_conditions),
            "ExpressionAttributeValues": _expression_attribute_values(key_conditions),
        }
    else:
        return {
            "KeyConditionExpression": _key_condition_expression(key_conditions),
            "FilterExpression": _filter_expression(filter),
            "ExpressionAttributeNames": _expression_attribute_names(filter),
            "ExpressionAttributeValues": {
                **_expression_attribute_values(key_conditions),
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
        key_conditions = {"pk": pk, "sk": sk or pk}
        clause = _key_and_filter_clause(key_conditions=key_conditions, filter=filter)
        response = self.dynamodb.query(TableName=self.table_name, **clause)
        try:
            (item,) = response["Items"]
        except (KeyError, ValueError):
            raise ItemNotFound("Item could not be found") from None
        return self.item_type(**item)

    @handle_dynamodb_errors()
    @log_action(
        log_reference=LogReference.REPOSITORY002,
        log_fields=["pk", "sk_name", "index_name", "pk_name", "sk"],
    )
    def _query(
        self,
        index_name,
        pk_name: str,
        pk: str,
        sk_name: str = None,
        sk: str = None,
        limit: int = PAGE_ITEM_LIMIT,
        exclusive_start_key: str = None,
        logger=None,
        **filter,
    ) -> PaginatedResponse:
        """
        Do not call this method directly, instead use `query` or `query_gsi_#` instead.
        """
        key_conditions = {pk_name: pk}
        if sk is not None:
            key_conditions[sk_name] = sk

        index_keys = list(set(("pk", "sk", pk_name)))  # dedupe if pk == pk_name
        if sk_name is not None:
            index_keys.append(sk_name)

        clause = _key_and_filter_clause(key_conditions=key_conditions, filter=filter)
        query_kwargs = {"TableName": self.table_name, "Limit": limit, **clause}
        if index_name is not None:
            query_kwargs["IndexName"] = index_name

        if exclusive_start_key is not None:
            exclusive_start_key = transform_next_page_token_to_start_key(
                exclusive_start_key
            )

        items, last_evaluated_key = [], None
        for item in self._scroll(
            index_keys=index_keys,
            query_kwargs=query_kwargs,
            exclusive_start_key=exclusive_start_key,
            logger=logger,
        ):
            if item is not None:  # means we haven't reached the final result yet
                if len(items) == PAGE_ITEM_LIMIT:
                    # never evaluated on the final page
                    last_item = items[-1]
                    last_evaluated_key = {
                        idx: getattr(last_item, idx).dict() for idx in index_keys
                    }
                    break
                items.append(item)

        if last_evaluated_key is not None:
            last_evaluated_key = transform_evaluation_key_to_next_page_token(
                last_evaluated_key
            )

        return PaginatedResponse(
            last_evaluated_key=last_evaluated_key, document_pointers=items
        )

    def _scroll(
        self,
        index_keys: str,
        query_kwargs: dict,
        exclusive_start_key: str,
        logger=None,
    ) -> Iterator[Union[DynamoDbModel, None]]:
        query_kwargs.pop("ExclusiveStartKey", None)
        if exclusive_start_key is not None:
            query_kwargs["ExclusiveStartKey"] = exclusive_start_key
        results = self.dynamodb.query(**query_kwargs)

        # Yield all valid items
        items: list[dict] = results["Items"]
        for item in items:
            try:
                _item = _is_record_valid(
                    item_type=self.item_type, item=item, logger=logger
                )
            except CorruptDocumentPointer:
                continue
            yield _item

        # Keep scrolling while there is still a LastEvaluatedKey
        last_evaluated_key = results.get("LastEvaluatedKey")
        if last_evaluated_key is not None:
            yield from self._scroll(
                index_keys=index_keys,
                query_kwargs=query_kwargs,
                exclusive_start_key=last_evaluated_key,
                logger=logger,
            )
        # Our own internal definition of there being no more results
        else:
            yield None

    def query(
        self,
        pk,
        sk=None,
        **filter,
    ) -> PaginatedResponse:
        """
        Query records using the main partition key
        """
        return self._query(None, "pk", pk, "sk", sk, **filter)

    def query_gsi_1(
        self,
        pk,
        sk=None,
        **filter,
    ) -> PaginatedResponse:
        """
        Query records using the Global Secondary Index 'idx_gsi_1'
        """
        return self._query("idx_gsi_1", "pk_1", pk, "sk_1", sk, **filter)

    def query_gsi_2(
        self,
        pk,
        sk=None,
        **filter,
    ) -> PaginatedResponse:
        """
        Query records using the Global Secondary Index 'idx_gsi_2'
        """
        return self._query("idx_gsi_2", "pk_2", pk, "sk_2", sk, **filter)

    def query_gsi_3(
        self,
        pk,
        sk=None,
        **filter,
    ) -> PaginatedResponse:
        """
        Query records using the Global Secondary Index 'idx_gsi_3'
        """
        return self._query("idx_gsi_3", "pk_3", pk, "sk_3", sk, **filter)

    def query_gsi_4(
        self,
        pk,
        sk=None,
        **filter,
    ) -> PaginatedResponse:
        """
        Query records using the Global Secondary Index 'idx_gsi_4'
        """
        return self._query("idx_gsi_4", "pk_4", pk, "sk_4", sk, **filter)

    def query_gsi_5(
        self,
        pk,
        sk=None,
        **filter,
    ) -> PaginatedResponse:
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
