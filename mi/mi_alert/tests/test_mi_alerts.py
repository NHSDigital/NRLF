import json
import time
from typing import Iterator
from uuid import uuid4

import pytest
from lambda_utils.logging import LogTemplate

from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json

SECONDS_TO_MILLISECONDS = 1000
LAMBDA_EXECUTION_TIME = 20 * SECONDS_TO_MILLISECONDS
SLEEP_TIME_SECONDS = 5


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

        yield from (event["message"] for event in response["events"])


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
    ),
)
@pytest.mark.integration
def test_mi_alert(error_event: dict, should_raise_alert: bool, s3_client, logs_client):
    # Setup
    start_time = int(time.time() * SECONDS_TO_MILLISECONDS)
    end_time = start_time + LAMBDA_EXECUTION_TIME

    tf_json = get_terraform_json()
    bucket_name = tf_json["mi"]["value"]["s3_mi_errors_bucket"]
    workspace = tf_json["workspace"]["value"]
    mi_metadata = tf_json["mi"]["value"]["mi_alert"]
    log_group_name = mi_metadata["log_group_name"]

    file_key = f"mi_alert_error_test/{str(uuid4())}"

    # INSERT INTO BUCKET
    s3_client.put_object(
        Bucket=bucket_name,
        Key=file_key,
        Body=json.dumps(error_event).encode(),
    )

    # Find evidence that the alert lambda was triggered by scanning the logs
    expected_event = json.dumps({"Event received by mi errors bucket": error_event})

    alert_found = False
    while (time.time() * SECONDS_TO_MILLISECONDS < end_time) and not alert_found:
        for message in trawl_logs(
            logs_client=logs_client,
            log_group_name=log_group_name,
            start_time=start_time,
        ):
            if message == expected_event:
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
