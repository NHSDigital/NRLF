from dataclasses import asdict
from typing import Union

import boto3
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecordEventName,
    DynamoDBStreamEvent,
)

from mi.stream_writer.event_handling import catch_error, insert_mi_record
from mi.stream_writer.model import (
    Action,
    DynamoDBEventConfig,
    DynamodbEventImageType,
    Environment,
    ErrorResponse,
    GoodResponse,
    RecordParams,
    SecretsManagerCache,
)
from mi.stream_writer.psycopg2 import psycopg2
from mi.stream_writer.utils import to_snake_case

EVENT_CONFIG = {
    DynamoDBRecordEventName.INSERT: DynamoDBEventConfig(
        image_type=DynamodbEventImageType.NEW_IMAGE,
        action=Action.CREATED,
    ),
    DynamoDBRecordEventName.REMOVE: DynamoDBEventConfig(
        image_type=DynamodbEventImageType.OLD_IMAGE,
        action=Action.DELETED,
    ),
}
SECRETSMANAGER_CLIENT = boto3.client("secretsmanager")
SECRETSMANAGER = SecretsManagerCache(client=SECRETSMANAGER_CLIENT)


@catch_error(log_fields=["event"])
def _handler(event) -> Union[GoodResponse, ErrorResponse]:
    event = DynamoDBStreamEvent(event)
    environment = Environment.construct()

    connection = psycopg2.connect(
        user=environment.POSTGRES_USERNAME,
        password=SECRETSMANAGER.get_secret(secret_id=environment.POSTGRES_PASSWORD),
        database=environment.POSTGRES_DATABASE_NAME,
        host=environment.RDS_CLUSTER_HOST,
        port=environment.RDS_CLUSTER_PORT,
    )
    cursor = connection.cursor()

    response = GoodResponse()
    for record in event.records:
        config = EVENT_CONFIG.get(record.event_name)
        if config is None:
            continue
        image_type = to_snake_case(config.image_type)
        document_pointer: dict = getattr(record.dynamodb, image_type)
        record = RecordParams.from_document_pointer(**document_pointer)
        response = insert_mi_record(record=record, sql=config.sql, cursor=cursor)
        if type(response) is ErrorResponse:
            break

    connection.commit()
    connection.close()

    return response


def handler(event, context=None):
    response = _handler(event=event)
    return asdict(response)
