import os
from enum import Enum
from pathlib import Path

import requests
from lambda_utils.logging import Logger, log_action, prepare_default_event_for_logging
from pydantic import BaseModel, Json


class Config(BaseModel):
    ENVIRONMENT: str
    SPLUNK_INDEX: str
    SOURCE: str
    SLACK_WEBHOOK_URL: Json[list[str]]


CONFIG = Config(
    **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
)

DUMMY_URL = "http://example.com"


class LogReference(Enum):
    PARSE_EVENT = "Parsing event"
    SEND_NOTIFICATION = "Sending notification"


@log_action(
    log_reference=LogReference.PARSE_EVENT,
    log_result=True,
    log_fields=["event"],
)
def parse_event(event: dict) -> tuple[str, str]:
    (record,) = event["Records"]
    bucket_name = record["s3"]["bucket"]["name"]
    file_key = record["s3"]["object"]["key"]
    return bucket_name, file_key


@log_action(
    log_reference=LogReference.SEND_NOTIFICATION,
    log_result=True,
    log_fields=["bucket_name", "file_key", "env", "slack_webhook_url"],
)
def send_notification(slack_webhook_url, **data):
    try:
        (slack_webhook_url,) = slack_webhook_url
    except ValueError:
        slack_webhook_url = DUMMY_URL

    response = requests.post(url=slack_webhook_url, json=data)
    return response.text


def handler(event: dict, context=None):
    logger = Logger(
        logger_name=Path(__file__).stem,
        aws_lambda_event=prepare_default_event_for_logging(),
        aws_environment=CONFIG.ENVIRONMENT,
        splunk_index=CONFIG.SPLUNK_INDEX,
        source=CONFIG.SOURCE,
    )
    bucket_name, file_key = parse_event(event=event, logger=logger)
    send_notification(
        slack_webhook_url=CONFIG.SLACK_WEBHOOK_URL,
        bucket_name=bucket_name,
        file_key=file_key,
        env=CONFIG.ENVIRONMENT,
        logger=logger,
    )
