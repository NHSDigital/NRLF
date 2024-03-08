import gzip

import requests
from lambda_utils.logging import log_action

from firehose.alert.constants import DUMMY_URL, FLAKY_SPLUNK_ERROR_CODES
from nrlf.core_pipeline.validators import json_loads
from nrlf.log_references import LogReference


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
    log_reference=LogReference.READ_BODY,
    log_result=False,
    log_fields=["bucket_name", "file_key"],
    sensitive=False,
)
def read_body(s3_client: str, bucket_name: str, file_key: str) -> bytes:
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    return response["Body"].read()


@log_action(
    log_reference=LogReference.PARSE_BODY,
    log_result=True,
)
def parse_event_body(body: bytes) -> list[dict]:
    raw_ndjson = gzip.decompress(body).decode()
    json_lines = filter(None, raw_ndjson.split("\n"))
    return list(map(json_loads, json_lines))


@log_action(
    log_reference=LogReference.IS_ERROR_EVENT,
    log_result=True,
)
def is_true_error_event(error_event: dict):
    if (  # These events will be retried, so no need to raise an alert
        error_event["errorCode"] in FLAKY_SPLUNK_ERROR_CODES
        and error_event.get("subsequenceNumber") == 0
    ):
        return False
    return True


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
