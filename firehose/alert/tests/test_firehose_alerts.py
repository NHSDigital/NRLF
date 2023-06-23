import gzip
import json
import time
from typing import Iterator, Literal

import pytest
from hypothesis import given
from hypothesis.strategies import builds
from lambda_utils.logging import LogTemplate
from pydantic import BaseModel, Field, ValidationError

from firehose.alert.steps import is_true_error_event
from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json

SECONDS_TO_MILLISECONDS = 1000
LAMBDA_EXECUTION_TIME = 20 * SECONDS_TO_MILLISECONDS
SLEEP_TIME_SECONDS = 5


class TrueErrorEvent(BaseModel):
    errorCode: str
    subsequenceNumber: int = Field(min=1)


class NotTrueErrorEvent(BaseModel):
    errorCode: Literal[
        "Splunk.ProxyWithoutStickySessions",
        "Splunk.ServerError",
        "Splunk.AckTimeout",
        "Splunk.ConnectionTimeout",
        "Splunk.ConnectionClosed",
        "Splunk.IndexerBusy",
    ]
    subsequenceNumber: Literal[0]


@given(error_event=builds(TrueErrorEvent))
def test_is_true_error_event(error_event: TrueErrorEvent):
    assert is_true_error_event(error_event=error_event.dict()), error_event


@given(error_event=builds(NotTrueErrorEvent))
def test_is_not_true_error_event(error_event: NotTrueErrorEvent):
    assert not is_true_error_event(error_event=error_event.dict()), error_event


def trawl_logs(
    logs_client, log_group_name: str, start_time: int
) -> Iterator[LogTemplate]:
    response = logs_client.describe_log_streams(
        logGroupName=log_group_name, orderBy="LastEventTime"
    )
    for log_stream in response["logStreams"]:
        response = logs_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream["logStreamName"],
            startTime=start_time,
            endTime=int(time.time() * SECONDS_TO_MILLISECONDS),
        )
        for event in response["events"]:
            try:
                yield LogTemplate.parse_raw(event["message"])
            except ValidationError:
                pass


@pytest.fixture(scope="session")
def session():
    tf_json = get_terraform_json()
    return new_aws_session(account_id=tf_json["assume_account_id"]["value"])


@pytest.fixture(scope="session")
def s3_client(session):
    return session.client("s3")


@pytest.fixture(scope="session")
def logs_client(session):
    return session.client("logs")


@pytest.mark.parametrize(
    ("error_event", "should_raise_alert"),
    (
        (
            {"errorCode": "foo"},
            True,
        ),
        (
            {"errorCode": "Splunk.ConnectionClosed", "subsequenceNumber": 1},
            True,
        ),
        (
            {"errorCode": "Splunk.ProxyWithoutStickySessions", "subsequenceNumber": 1},
            True,
        ),
        (
            {"errorCode": "Splunk.IndexerBusy", "subsequenceNumber": 1},
            True,
        ),
        (
            {"errorCode": "Splunk.ConnectionClosed", "subsequenceNumber": 0},
            False,
        ),
        (
            {"errorCode": "Splunk.ProxyWithoutStickySessions", "subsequenceNumber": 0},
            False,
        ),
        (
            {"errorCode": "Splunk.IndexerBusy", "subsequenceNumber": 0},
            False,
        ),
    ),
)
@pytest.mark.integration
def test_firehose_alert(
    error_event: dict, should_raise_alert: bool, s3_client, logs_client
):
    # Setup
    start_time = int(time.time() * SECONDS_TO_MILLISECONDS)
    end_time = start_time + LAMBDA_EXECUTION_TIME

    tf_json = get_terraform_json()
    firehose_metadata = tf_json["firehose"]["value"]["processor"]
    s3_metadata = firehose_metadata["delivery_stream"]["s3"]
    log_group_name = firehose_metadata["alert"]["log_group_name"]
    workspace = tf_json["workspace"]["value"]

    # Trigger an alert by creating a file with prefix "errors" in the firehose bucket
    bucket_name = s3_metadata["arn"].replace("arn:aws:s3:::", "")
    file_key = f"errors/test-{start_time}"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=file_key,
        Body=gzip.compress(json.dumps(error_event).encode()),
    )

    # Find evidence that the alert lambda was triggered by scanning the logs
    expected_event = {
        "slack_webhook_url": [],
        "bucket_name": bucket_name,
        "file_key": file_key,
        "env": workspace,
    }

    alert_found = False
    while (time.time() * SECONDS_TO_MILLISECONDS < end_time) and not alert_found:
        for message in trawl_logs(
            logs_client=logs_client,
            log_group_name=log_group_name,
            start_time=start_time,
        ):
            if message.data.inputs == expected_event:
                alert_found = True
                break
        time.sleep(SLEEP_TIME_SECONDS)

    if should_raise_alert:
        assert (
            alert_found
        ), f"Could not find data\n\n{expected_event}\n\nin log group '{log_group_name}'"
    else:
        assert (
            not alert_found
        ), f"Unexpectedly found data\n\n{expected_event}\n\nin log group '{log_group_name}'"
