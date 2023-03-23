import time
from datetime import datetime
from typing import Iterator

from lambda_utils.logging import LogData, LogTemplate
from nrlf.core.firehose.model import (
    CloudwatchLogsData,
    CloudwatchMessageType,
    FirehoseSubmissionRecord,
    LogEvent,
)
from nrlf.core.firehose.submission import FirehoseClient, _submit_records
from nrlf.core.firehose.utils import name_from_arn

from helpers.firehose import fetch_logs_from_s3

SLEEP_SECONDS = 15
MAX_RUNTIME = 400


def parse_prefix(prefix: str, time: datetime) -> str:
    return (
        prefix.replace("!{timestamp:yyyy}", str(time.year))
        .replace("!{timestamp:MM}", str(time.month).zfill(2))
        .replace("!{timestamp:dd}", str(time.day).zfill(2))
        .replace("!{timestamp:HH}", str(time.hour).zfill(2))
    )


def _make_good_log(transaction_id) -> str:
    return LogTemplate(
        correlation_id="123",
        nhsd_correlation_id="abc",
        transaction_id=transaction_id,
        host="test",
        environment="test",
        request_id="123",
        log_reference="FOO.BAR",
        log_level="INFO",
        outcome="GOOD",
        duration_ms=123,
        message="all good",
        data=LogData(function="foo.bar", inputs={"some": "input"}, result="a result"),
        error="oops",
        call_stack="oops again",
        timestamp="123",
        sensitive=True,
    ).json()


def make_good_cloudwatch_data(transaction_id, n_logs=10):
    good_log_event = LogEvent(
        id="123",
        timestamp=123,
        message=_make_good_log(transaction_id=transaction_id),
    )
    return CloudwatchLogsData(
        record_id="dummy_id",
        logEvents=[good_log_event] * n_logs,
        messageType=CloudwatchMessageType.NORMAL_LOG_EVENT,
        owner="nrlf",
        logGroup="nrlf-test-group",
        logStream="nrlf-test-stream",
    )


def submit_cloudwatch_data_to_firehose(
    session, stream_arn, cloudwatch_data
) -> datetime:
    stream_name = name_from_arn(arn=stream_arn)
    firehose_client = FirehoseClient(
        client=session.client("firehose"), stream_name=stream_name
    )

    records = [FirehoseSubmissionRecord(Data=cloudwatch_data.encode())]
    response = _submit_records(firehose_client=firehose_client, records=records)
    assert response.failed_put_count == 0, "This is probably a transient error"
    return datetime.utcnow()


def _trawl_s3_for_matching_files(
    s3_client, bucket_name: str, prefix: str, start_time: datetime
) -> Iterator[list[dict]]:
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    for file_metadata in response.get("Contents", []):
        if file_metadata["LastModified"] < start_time.astimezone():
            continue
        yield file_metadata["Key"]


def retrieve_firehose_output(
    s3_client,
    bucket_name: str,
    start_time: datetime,
    possible_prefixes: list[str],
) -> list[dict]:
    while (datetime.utcnow() - start_time).total_seconds() < MAX_RUNTIME:
        time.sleep(SLEEP_SECONDS)
        for prefix in possible_prefixes:
            for file_key in _trawl_s3_for_matching_files(
                s3_client=s3_client,
                bucket_name=bucket_name,
                prefix=prefix,
                start_time=start_time,
            ):
                logs_from_s3 = fetch_logs_from_s3(
                    s3_client=s3_client,
                    bucket_name=bucket_name,
                    file_key=file_key,
                )
                yield prefix, logs_from_s3

    # If no break by now then assume the search has failed
    raise RuntimeError(
        "\n".join(
            (
                "Could not find matching output files in bucket:",
                bucket_name,
                "with any of key prefixes:",
                "\nor\n".join(possible_prefixes),
                f"after {MAX_RUNTIME} seconds of submitting events to firehose at time",
                start_time.isoformat(),
            )
        )
    )


def all_logs_are_on_s3(original_logs: list[dict], logs_from_s3: list[dict]) -> bool:
    return all(log in logs_from_s3 for log in original_logs)
