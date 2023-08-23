import json
from dataclasses import asdict

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
    MiResponses,
    RecordParams,
    SecretsManagerCache,
)
from mi.stream_writer.psycopg2 import psycopg2
from mi.stream_writer.utils import is_document_pointer, to_snake_case

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
S3_CLIENT = boto3.client("s3")


@catch_error(log_fields=["event"])
def _handler(
    event,
    responses: MiResponses,
    environment: Environment,
    secrets_manager: SecretsManagerCache,
) -> MiResponses:
    event = DynamoDBStreamEvent(event)

    connection = psycopg2.connect(
        user=environment.POSTGRES_USERNAME,
        password=secrets_manager.get_secret(secret_id=environment.POSTGRES_PASSWORD),
        database=environment.POSTGRES_DATABASE_NAME,
        host=environment.RDS_CLUSTER_HOST,
        port=environment.RDS_CLUSTER_PORT,
    )
    cursor = connection.cursor()

    for record in event.records:
        if not is_document_pointer(**record.dynamodb.keys):
            continue

        config = EVENT_CONFIG.get(record.event_name)
        if config is None:
            continue

        image_type = to_snake_case(config.image_type)
        document_pointer: dict = getattr(record.dynamodb, image_type)

        record_params = RecordParams.from_document_pointer(**document_pointer)

        sql = config.sql

        insert_mi_record(
            record_params=record_params, sql=sql, cursor=cursor, responses=responses
        )

    connection.close()


@catch_error(log_fields=["responses"])
def send_errors_to_s3(responses: MiResponses, environment: Environment, s3_client):
    unique_id = responses.unique_id

    for response in responses.error_responses:
        key = unique_id
        if response.metadata["event"]:
            key += f'/{response.metadata["event"]["Records"][0]["eventID"]}'

        s3_client.put_object(
            Bucket=environment.MI_S3_ERROR_BUCKET,
            Key=f"{key}.json",
            Body=json.dumps(asdict(response)).encode(),
        )


def handler(
    event, context=None, secrets_manager=None, s3_client=None, environment=None
):

    if secrets_manager is None:
        secrets_manager = SECRETSMANAGER

    if s3_client is None:
        s3_client = S3_CLIENT

    if environment is None:
        environment = Environment.construct()

    responses = MiResponses()

    _handler(
        event=event,
        responses=responses,
        environment=environment,
        secrets_manager=secrets_manager,
    )
    send_errors_to_s3(responses=responses, environment=environment, s3_client=s3_client)

    successful_responses = [
        asdict(response) for response in responses.successful_responses
    ]
    error_responses = [asdict(response) for response in responses.error_responses]

    print("Successful responses", len(successful_responses))  # noqa
    print("Failed responses", len(error_responses))  # noqa
    return asdict(responses)
