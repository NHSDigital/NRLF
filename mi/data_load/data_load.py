from typing import Generator, Iterator

import fire
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecordEventName,
)

from helpers.aws_session import new_session_from_env
from mi.reporting.actions import perform_query
from mi.reporting.resources import get_credentials, get_rds_endpoint
from mi.sql_query.model import Sql, SqlQueryEvent
from mi.stream_writer.model import DynamodbEventImageType
from mi.stream_writer.utils import invoke_stream_writer
from nrlf.core.constants import DbPrefix
from nrlf.core.types import DynamoDbClient

# Limits from https://docs.aws.amazon.com/lambda/latest/dg/with-ddb.html
MAX_ITEMS_PER_CHUNK = 10, 000
MAX_CHUNK_SIZE_BYTES = int(6000000 * 0.95)  # 95% of 6MB
from aws_lambda_powertools.utilities.parser.models.dynamodb import (
    DynamoDBStreamChangedRecordModel,
    DynamoDBStreamModel,
    DynamoDBStreamRecordModel,
)

KEYS = set(("pk", "sk"))
EVENT_SOURCE = "aws:dynamodb"


class ItemTooLarge(Exception):
    pass


class MiTableNotEmpty(Exception):
    pass


def item_to_stream_record(item: dict) -> dict:
    return DynamoDBStreamRecordModel(
        eventID="",
        awsRegion="eu-west-2",
        eventSourceARN="",
        eventName=DynamoDBRecordEventName.INSERT.name,
        eventVersion=0,
        eventSource=EVENT_SOURCE,
        dynamodb=DynamoDBStreamChangedRecordModel(
            Keys={k: v for k, v in item.items() if k in KEYS},
            NewImage=item,
            SequenceNumber=0,
            SizeBytes=0,
            StreamViewType=DynamodbEventImageType.NEW_IMAGE.name,
        ),
    )


def get_table_name(workspace: str):
    return f"nhsd-nrlf--{workspace}--document-pointer"


def get_mi_item_count(session, env, workspace):
    credentials = get_credentials(session=session, workspace=workspace)
    endpoint = get_rds_endpoint(session=session, env=env)
    statement = "SELECT * FROM fact.measure"
    event = SqlQueryEvent(
        sql=Sql(statement=statement),
        endpoint=endpoint,
        **credentials,
    )

    return perform_query(session=session, workspace=workspace, event=event)


def _get_item_size(
    item: DynamoDBStreamRecordModel, item_idx: int, max_chunk_size_bytes: int
):
    item_size = len(item.json().encode())
    if item_size > max_chunk_size_bytes:
        raise ItemTooLarge(
            f"Item {item_idx} has size {item_size}B, which "
            f"exceeds the maximum chunk size of {max_chunk_size_bytes}B"
        )
    return item_size


def chunk_by_event_size(
    items: Iterator[DynamoDBStreamRecordModel],
    max_items_per_chunk: int,
    max_chunk_size_bytes: int,
) -> Generator[list[DynamoDBStreamRecordModel], None, None]:
    current_chunk = []
    current_chunk_size = 0

    for i, item in enumerate(items):
        item_size = _get_item_size(
            item=item, item_idx=i, max_chunk_size_bytes=max_chunk_size_bytes
        )
        if (
            len(current_chunk) == max_items_per_chunk
            or current_chunk_size + item_size > max_chunk_size_bytes
        ):
            yield current_chunk
            current_chunk = []
            current_chunk_size = 0

        current_chunk.append(item)
        current_chunk_size += item_size

    if current_chunk:
        yield current_chunk


def _scan(client: DynamoDbClient, table_name: str):
    start_key_kwargs = {}
    while True:
        response = client.scan(TableName=table_name, **start_key_kwargs)
        yield from response["Items"]
        try:
            start_key_kwargs = {"ExclusiveStartKey": response["LastEvaluatedKey"]}
        except KeyError:
            break


def scan(
    client: DynamoDbClient,
    table_name: str,
    pk_prefix: str,
    max_items_per_chunk: int = MAX_ITEMS_PER_CHUNK,
    max_chunk_size_bytes: int = MAX_CHUNK_SIZE_BYTES,
):
    all_items = _scan(client=client, table_name=table_name)
    filtered_items = filter(
        lambda item: item["pk"]["S"].startswith(pk_prefix), all_items
    )
    stream_items = map(item_to_stream_record, filtered_items)
    yield from chunk_by_event_size(
        items=stream_items,
        max_items_per_chunk=max_items_per_chunk,
        max_chunk_size_bytes=max_chunk_size_bytes,
    )


def data_load(env: str, workspace: str = None):
    print("Starting the process for the MI dataload...")  # noqa: T201

    session = new_session_from_env(env=env)
    client = session.client("dynamodb")
    table_name = get_table_name(workspace=workspace)

    item_count = get_mi_item_count(session=session, env=env, workspace=workspace)

    if len(item_count) > 0:
        raise MiTableNotEmpty("The MI table is not empty")
    for records in scan(
        client=client, table_name=table_name, pk_prefix=DbPrefix.DocumentPointer
    ):
        event = DynamoDBStreamModel(Records=records)
        invoke_stream_writer(session=session, workspace=workspace, event=event.dict())

    print("Data load complete")  # noqa: T201


if __name__ == "__main__":
    fire.Fire(data_load)
