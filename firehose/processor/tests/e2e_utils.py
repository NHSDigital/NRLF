import time
from copy import deepcopy
from datetime import datetime
from itertools import chain
from typing import Iterator

from lambda_utils.logging import LogData, LogTemplate

from helpers.firehose import fetch_logs_from_s3
from nrlf.core_pipeline.firehose.model import (
    CloudwatchLogsData,
    CloudwatchMessageType,
    LogEvent,
)

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
        index="splunk_index",
        source="source",
        function="test.function",
        request_id="123",
        log_reference="FOO.BAR",
        log_level="INFO",
        outcome="GOOD",
        duration_ms=123,
        message="all good",
        data=LogData(inputs={"some": "input"}, result="a result"),
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
        messageType=CloudwatchMessageType.DATA_MESSAGE,
        owner="nrlf",
        logGroup="nrlf-test-group",
        logStream="nrlf-test-stream",
    )


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
                if prefix.startswith("error"):
                    logs_from_s3 = list(chain(logs_from_s3))  # Flatten list of lists

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


def all_logs_are_on_s3(
    original_logs: list[dict],
    logs_from_s3: list[dict],
    good_event=False,
    redacted=False,
) -> bool:
    for log in original_logs:
        _log = deepcopy(log)
        _logs_from_s3 = logs_from_s3
        if good_event:
            # Pull log out from nested Splunk Event
            _logs_from_s3 = [_log_from_s3["event"] for _log_from_s3 in logs_from_s3]
        if redacted:
            _log["data"] = "REDACTED"
        if _log not in _logs_from_s3:
            return False
    return True
