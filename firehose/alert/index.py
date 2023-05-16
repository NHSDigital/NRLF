import os
from pathlib import Path

import boto3
from lambda_utils.logging import Logger, prepare_default_event_for_logging
from pydantic import BaseModel, Json

from firehose.alert.steps import (
    is_true_error_event,
    parse_event,
    parse_event_body,
    read_body,
    send_notification,
)


class Config(BaseModel):
    ENVIRONMENT: str
    SPLUNK_INDEX: str
    SOURCE: str
    SLACK_WEBHOOK_URL: Json[list[str]]


CONFIG = Config(
    **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
)
S3_CLIENT = boto3.client("s3")


def handler(event: dict, context=None):
    logger = Logger(
        logger_name=Path(__file__).stem,
        aws_lambda_event=prepare_default_event_for_logging(),
        aws_environment=CONFIG.ENVIRONMENT,
        splunk_index=CONFIG.SPLUNK_INDEX,
        source=CONFIG.SOURCE,
    )
    bucket_name, file_key = parse_event(event=event, logger=logger)
    body = read_body(
        s3_client=S3_CLIENT, bucket_name=bucket_name, file_key=file_key, logger=logger
    )
    error_events = parse_event_body(body=body, logger=logger)
    if any(
        is_true_error_event(error_event=error_event, logger=logger)
        for error_event in error_events
    ):
        send_notification(
            slack_webhook_url=CONFIG.SLACK_WEBHOOK_URL,
            bucket_name=bucket_name,
            file_key=file_key,
            env=CONFIG.ENVIRONMENT,
            logger=logger,
        )
