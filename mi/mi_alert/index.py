import json
import os

import boto3
from pydantic import BaseModel, Json

from mi.mi_alert.steps import parse_event, read_body, send_notification

PENVS = {"dev", "int", "ref", "prod"}


class Config(BaseModel):
    ENVIRONMENT: str
    SOURCE: str
    SLACK_WEBHOOK_URL: Json[list[str]]


CONFIG = Config(
    **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
)
S3_CLIENT = boto3.client("s3")


def handler(event: dict, context=None):

    bucket_name, file_key = parse_event(event=event)
    body = read_body(s3_client=S3_CLIENT, bucket_name=bucket_name, file_key=file_key)
    if CONFIG.ENVIRONMENT in PENVS:
        send_notification(
            slack_webhook_url=CONFIG.SLACK_WEBHOOK_URL,
            bucket_name=bucket_name,
            file_key=file_key,
            env=CONFIG.ENVIRONMENT,
        )
    else:
        print(  # noqa:T201
            json.dumps({"Event received by mi errors bucket": json.loads(body)}), end=""
        )
