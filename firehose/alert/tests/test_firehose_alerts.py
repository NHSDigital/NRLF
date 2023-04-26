import time
from typing import Iterator

import pytest
from lambda_utils.logging import LogTemplate
from pydantic import ValidationError

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
        for event in response["events"]:
            try:
                yield LogTemplate.parse_raw(event["message"])
            except ValidationError:
                pass


@pytest.mark.integration
def test_firehose_alert():
    # Setup
    start_time = int(time.time() * SECONDS_TO_MILLISECONDS)
    end_time = start_time + LAMBDA_EXECUTION_TIME

    tf_json = get_terraform_json()
    firehose_metadata = tf_json["firehose"]["value"]["processor"]
    s3_metadata = firehose_metadata["delivery_stream"]["s3"]
    log_group_name = firehose_metadata["alert"]["log_group_name"]
    workspace = tf_json["workspace"]["value"]
    session = new_aws_session(account_id=tf_json["assume_account_id"]["value"])

    # Trigger an alert by creating a file with prefix "errors" in the firehose bucket
    bucket_name = s3_metadata["arn"].replace("arn:aws:s3:::", "")
    file_key = f"errors/test-{start_time}"
    session.client("s3").put_object(Bucket=bucket_name, Key=file_key)

    # Find evidence that the alert lambda was triggered by scanning the logs
    expected_event = {
        "slack_webhook_url": [],
        "bucket_name": bucket_name,
        "file_key": file_key,
        "env": workspace,
    }

    logs_client = session.client("logs")
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
    assert (
        alert_found
    ), f"Could not find data\n\n{expected_event}\n\nin log group '{log_group_name}'"
