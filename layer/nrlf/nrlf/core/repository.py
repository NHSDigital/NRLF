from functools import reduce, wraps
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Literal,
    Optional,
    TypeVar,
    Union,
)

from botocore.exceptions import ClientError
from lambda_utils.logging import add_log_fields, log_action
from pydantic import ValidationError

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
from nrlf.core.types import DynamoDBClient
from nrlf.log_references import LogReference
from nrlf.producer.fhir.r4.model import RequestQueryType

PydanticModel = TypeVar("PydanticModel", bound=DynamoDbModel)

MAX_TRANSACT_ITEMS = 100
PAGE_ITEM_LIMIT = 20
COUNT_ITEM_LIMIT = 100  # Larger paging size for _count endpoint for performance
ATTRIBUTE_EXISTS_PK = "attribute_exists(pk)"
ATTRIBUTE_NOT_EXISTS_PK = "attribute_not_exists(pk)"
CONDITION_CHECK_CODES = [
    "ConditionalCheckFailedException",
    "TransactionCanceledException",
    "ValidationException",
]


class CorruptItem(Exception):
    pass


def _strip_none(dictionary: Optional[dict]) -> Optional[dict]:
    """
    Removes key-value pairs with None values from a dictionary.
    """
    if dictionary is None:
        return None
    return {key: value for (key, value) in dictionary.items() if value is not None}


def custodian_filter(
    custodian_identifier: Optional[RequestQueryCustodian],
) -> Optional[str]:
    """
    Extracts the custodian identifier from the given RequestQueryCustodian object.
    """
    if custodian_identifier is None:
        return None

    return custodian_identifier.root.split("|", 1)[1]


def type_filter(type_identifier: Optional[RequestQueryType], pointer_types):
    if type_identifier is not None:
        return [type_identifier.root]

    return pointer_types


def _handle_dynamodb_errors(
    function: Callable, conditional_check_error_message: str = "", error_type=Exception
) -> Callable:
    """
    Decorator function that handles DynamoDB errors by catching ClientError exceptions and
    raising appropriate error types based on the error code.
    """

    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ClientError as error:
            error_code = None
            if response := error.response.get("Error"):
                error_code = response.get("Code")

            if error_code in CONDITION_CHECK_CODES:
                raise error_type(
                    f"Condition check failed - {conditional_check_error_message or error_code}"
                )
            raise Exception(f"There was an error with the database: {error}")

    return wrapper


@log_action(log_reference=LogReference.REPOSITORY001)
def _is_record_valid(item_type: type[DynamoDbModel], item: dict):
    """
    Checks if a record is valid by attempting to parse it using the provided item_type.
    """
    valid = True
    try:
        return item_type(**item)
    except (ValueError, ValidationError):
        valid = False
        raise CorruptItem(
            f"Cannot parse '{item_type.__name__}' - this item may be corrupt. "
            f"Skipping failed item: {item}"
        )
    finally:
        add_log_fields(valid=valid)


def _keys(
    primary_key: str,
    secondary_key: str,
    primary_key_name: str = "pk",
    secondary_key_name: str = "sk",
):
    """
    Generate a dictionary of keys for a primary key and an optional secondary key.

    Example:
        >>> _keys("user123", "profile")
        {'pk': 'user123', 'sk': 'profile'}
    """
    keys = {primary_key_name: {"S": f"{primary_key}"}}
    if secondary_key is not None:
        keys[secondary_key_name] = {"S": f"{secondary_key}"}
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


def _encode(value: Any) -> dict:
    """
    Encodes a value into a DynamoDB object.

    Example: 123 -> { "N": 123 }
    """
    encode_type = DYNAMODB_ENCODE_LOOKUP[type(value)]
    if encode_type == "NULL":
        return {"NULL": True}
    if encode_type == "M":
        return {"M": {key: _encode(val) for (key, val) in value.items()}}
    return {encode_type: value}


def _decode_dict(dynamodb_map: Dict[Literal["M"], Dict[str, Any]]) -> Dict[str, Any]:
    """
    Recursively decodes a DynamoDB map
    """
    return {key: _decode(value) for (key, value) in dynamodb_map["M"].items()}


def _decode_list(dynamodb_list: Dict[Literal["L"], List[Any]]) -> List[Any]:
    """
    Recursively decodes a DynamoDB list
    """
    return [_decode(value) for value in dynamodb_list["L"]]


def _decode_number(node: Dict[Literal["N"], str]) -> Union[int, float]:
    """
    Tries to maintain integer precision by guessing
    """
    float_value = float(node["N"])
    int_value = int(float_value)
    return int_value if int_value == float_value else float_value


DYNAMODB_DECODE_LOOKUP = {
    "NULL": lambda _: None,
    "B": lambda node: bool(node["B"]),
    "S": lambda node: str(node["S"]),
    "N": _decode_number,
    "M": _decode_dict,
    "L": _decode_list,
}


def _decode(node: dict) -> Any:
    """
    decodes a dynamodb object into a value

    e.g. {"N":123} -> 123
    """
    key = "".join(node.keys()).upper()
    fn = DYNAMODB_DECODE_LOOKUP[key]
    if fn:
        return fn(node)
    raise Exception(f"Unhandled DynamoDb type: {key}")


def _key_condition_expression(key_values: dict) -> str:
    """
    Used to generate the 'KeyConditionExpression' parameter in dynamodb queries.
    It delivers a simpler interface by reducing the number of operators to
    'AND', '=' and 'in' as those are the only ones we use.

    { "foo": 123, "bar": "green" } -> "foo = :foo" AND bar = :bar"
    """
    return " AND ".join(
        [
            f"{key} = :{key}"
            for (key, value) in key_values.items()
            if f"{value}" != "None"
        ]
    )


def _filter_expression(filters: dict) -> str:
    """
    Used to generate the 'FilterExpression' parameter in dynamodb queries. It
    delivers a simpler interface by reducing the number of operators to
    'AND', '=' and 'in' as those are the only ones we use.

    { "foo": 123, "bar": "green" } -> "#foo = :foo AND #bar = :bar"
    """

    def _item(key: str, value: Any) -> str:
        if isinstance(value, list):
            items = ", ".join([f":{key}_{ix}" for ix in range(1, len(value) + 1)])
            return f"#{key} in ({items})"
        return f"#{key} = :{key}"

    return " AND ".join([_item(key, value) for (key, value) in filters.items()])


def _expression_attribute_names(attributes: dict) -> dict:
    """
    Used to generate the 'ExpressionAttributeNames' parameter in dynamodb
    queries.

    { "foo": "123", "bar": "green" } -> { "#foo": "foo", "#bar": "bar" }
    """
    return {f"#{key}": key for key in attributes}


def _expression_attribute_values(attributes: dict) -> dict:
    """
    Used to generate the 'ExpressionAttributeValues' parameter in dynamodb
    queries.

    { "foo": 123, "bar": "green" } -> { ":foo": 123, ":bar": "green" }
    """

    def _encode_value(key: str, value: Any) -> Dict[str, Any]:
        if isinstance(value, list):
            return {f":{key}_{ix+1}": _encode(item) for ix, item in enumerate(value)}
        return {f":{key}": _encode(value)}

    return reduce(
        lambda a, b: ({**a, **b}),
        [_encode_value(key, value) for (key, value) in attributes.items()],
        {},
    )


def _key_and_filter_clause(key_conditions: dict, filter: Optional[dict] = None):
    """
    Constructs the key and filter clause for a DynamoDB query.
    """
    filter = _strip_none(filter)
    if not filter:
        return {
            "KeyConditionExpression": _key_condition_expression(key_conditions),
            "ExpressionAttributeValues": _expression_attribute_values(key_conditions),
        }

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
    conditional_check_error_message: str = "",
    error_type: type[Exception] = DynamoDbError,
):
    return lambda function: _handle_dynamodb_errors(
        function,
        conditional_check_error_message=conditional_check_error_message,
        error_type=error_type,
    )


class Repository(Generic[PydanticModel]):
    """
    A generic repository class for interacting with a DynamoDB table.

    Args:
        item_type (type[PydanticModel]): The type of the Pydantic model used for items in the table.
        client (DynamoDbClient): The DynamoDB client used for database operations.
        environment_prefix (str, optional): Prefix for the table name, used for environment separation. Defaults to "".
    """

    def __init__(
        self,
        item_type: type[PydanticModel],
        client: DynamoDBClient,
        environment_prefix: str = "",
    ):
        self.dynamodb = client
        self.item_type = item_type
        self.table_name = environment_prefix + item_type.kebab()

    @handle_dynamodb_errors(
        conditional_check_error_message="Duplicate item", error_type=DuplicateError
    )
    def create(self, item: PydanticModel):
        return self.dynamodb.put_item(
            TableName=self.table_name,
            Item=item.model_dump(),
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
        )

    # @deprecated("Use `get` instead.")
    # @handle_dynamodb_errors()
    # def read(self, KeyConditionExpression: str, **kwargs) -> PydanticModel:
    #     response = self.dynamodb.query(
    #         TableName=self.table_name,
    #         KeyConditionExpression=KeyConditionExpression,
    #         **kwargs,
    #     )
    #     try:
    #         (item,) = response["Items"]
    #     except (KeyError, ValueError):
    #         raise ItemNotFound("Item could not be found") from None
    #     return self.item_type(**item)

    @handle_dynamodb_errors()
    def read_item(
        self,
        pk: str,
        sk: Optional[str] = None,
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
        index_name: Optional[str],
        pk_name: str,
        pk: str,
        sk_name: Optional[str] = None,
        sk: Optional[str] = None,
        limit: int = PAGE_ITEM_LIMIT,
        exclusive_start_key: Optional[str] = None,
        logger=None,
        **filter,
    ) -> PaginatedResponse:
        """
        Do not call this method directly, instead use `query` or `query_gsi_#` instead.
        """
        key_conditions = {pk_name: pk}
        if sk is not None and sk_name is not None:
            key_conditions[sk_name] = sk

        index_keys = list(set(("pk", "sk", pk_name)))  # dedupe if pk == pk_name
        if sk_name is not None:
            index_keys.append(sk_name)

        clause = _key_and_filter_clause(key_conditions=key_conditions, filter=filter)
        query_kwargs = {"TableName": self.table_name, **clause}
        if limit is not None and limit > 0:
            query_kwargs["Limit"] = limit
        if index_name is not None:
            query_kwargs["IndexName"] = index_name

        if exclusive_start_key is not None:
            exclusive_start_key = transform_next_page_token_to_start_key(
                exclusive_start_key
            )

        items, last_evaluated_key = [], None
        for item in self._scroll(
            query_kwargs=query_kwargs,
            exclusive_start_key=exclusive_start_key,
            logger=logger,
        ):
            if item is not None:  # means we haven't reached the final result yet
                if len(items) == limit:
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
        add_log_fields(count=len(items))

        return PaginatedResponse(last_evaluated_key=last_evaluated_key, items=items)

    def _scroll(
        self,
        query_kwargs: dict,
        exclusive_start_key: str,
        logger=None,
    ) -> Iterator[Union[DynamoDbModel, None]]:
        """
        Scroll through the DynamoDB table using the provided query parameters.

        Args:
            query_kwargs (dict): The query parameters for the DynamoDB query.
            exclusive_start_key (str): The exclusive start key for pagination.
            logger (Optional): The logger object for logging.

        Yields:
            Iterator[Union[DynamoDbModel, None]]: An iterator of DynamoDB items or None.
        """
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
            except CorruptItem:
                continue
            yield _item

        # Keep scrolling while there is still a LastEvaluatedKey
        last_evaluated_key = results.get("LastEvaluatedKey")
        if last_evaluated_key is not None:
            yield from self._scroll(
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
        sk_name = None if sk is None else "sk"
        return self._query(
            index_name=None, pk_name="pk", pk=pk, sk_name=sk_name, sk=sk, **filter
        )

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
    def update(self, item: PydanticModel):
        """
        Update a single Record
        """
        args = {
            "TableName": self.table_name,
            "Item": item.model_dump(),
            "ConditionExpression": "attribute_exists(pk) AND attribute_exists(sk)",
        }
        return self.dynamodb.put_item(**args)

    @handle_dynamodb_errors(
        conditional_check_error_message="Supersede ID mismatch",
        error_type=SupersedeError,
    )
    def supersede(self, create_item: PydanticModel, delete_pks: list[str]):
        """
        Creates a new Record and delete existing records in a single transaction
        """

        def _delete(id_: str):
            return {
                "Delete": {
                    "TableName": self.table_name,
                    "ConditionExpression": "attribute_exists(pk) AND attribute_exists(sk)",
                    "Key": _keys(id_, id_),
                }
            }

        if len(delete_pks) >= MAX_TRANSACT_ITEMS:
            raise TooManyItemsError("Too many items to process in one transaction")

        transact_items = [_delete(id) for id in delete_pks] + [
            self._put_statement(item=create_item)
        ]

        try:
            return self.dynamodb.transact_write_items(TransactItems=transact_items)

        except ClientError as error:
            if "CancellationReasons" in error.response:
                reasons = error.response["CancellationReasons"]
                for ix, reason in enumerate(reasons):
                    if (
                        reason["Code"] == "ConditionalCheckFailed"
                        and "Put" in transact_items[ix]
                    ):
                        raise DuplicateError("Condition check failed - Duplicate item")
            raise error

    @handle_dynamodb_errors(conditional_check_error_message="Forbidden")
    def hard_delete(self, primary_key, secondary_key=None):
        keys = _keys(
            primary_key, secondary_key or primary_key
        )  # if no SK then the table uses same value of SK as PK.

        args = {
            "TableName": self.table_name,
            "Key": keys,
            "ConditionExpression": "attribute_exists(pk) AND attribute_exists(sk)",
        }
        return self.dynamodb.delete_item(**args)

    @handle_dynamodb_errors(
        conditional_check_error_message="Duplicate item", error_type=DuplicateError
    )
    def upsert_many(self, items: list[PydanticModel]):
        """Creates many new Records in a single transaction"""

        transact_items = list(
            map(lambda item: self._put_statement(item, force_create=True), items)
        )
        return self.dynamodb.transact_write_items(TransactItems=transact_items)

    def _put_statement(
        self, item: PydanticModel, force_create=False
    ) -> dict[str, dict[str, Any]]:
        condition_kwargs = (
            {
                "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
            }
            if not force_create
            else {}
        )
        return {
            "Put": {
                "TableName": self.table_name,
                "Item": item.model_dump(),
                **condition_kwargs,
            }
        }
