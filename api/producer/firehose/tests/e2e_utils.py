import base64
import gzip
import json
import time
from datetime import datetime
from functools import cache
from itertools import chain
from typing import Iterator

from lambda_utils.logging import LogTemplate
from nrlf.core.firehose.model import (
    CloudwatchLogsData,
    CloudwatchMessageType,
    FirehoseSubmissionRecord,
)
from nrlf.core.firehose.submission import FirehoseClient, _submit_records
from nrlf.core.firehose.utils import name_from_arn

SLEEP_SECONDS = 15
MAX_RUNTIME = 400


def parse_prefix(prefix: str, time: datetime) -> str:
    return (
        prefix.replace("!{timestamp:yyyy}", str(time.year))
        .replace("!{timestamp:MM}", str(time.month).zfill(2))
        .replace("!{timestamp:dd}", str(time.day).zfill(2))
        .replace("!{timestamp:HH}", str(time.hour).zfill(2))
    )


def _make_good_logs(transaction_id, n_logs):
    return [
        LogTemplate(
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
            data={"some": "data"},
            error="oops",
            call_stack="oops again",
            timestamp="123",
            sensitive=True,
        )
    ] * n_logs


def make_good_cloudwatch_data(transaction_id, n_logs=10):
    return CloudwatchLogsData(
        record_id="dummy_id",
        logEvents=_make_good_logs(transaction_id=transaction_id, n_logs=n_logs),
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


def _parse_error_event(error_event: dict):
    cloudwatch_event = json.loads(
        gzip.decompress(base64.b64decode(error_event["rawData"]))
    )
    yield from cloudwatch_event["logEvents"]


@cache
def _fetch_logs_from_s3(s3_client, bucket_name, file_key) -> list[dict]:
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    print("Retrieving data from ", bucket_name, file_key)
    with gzip.open(response["Body"], "rt") as gf:
        data = gf.read()

    file_lines = filter(bool, data.split("\n"))  # Newline delimited json
    parsed_lines = map(json.loads, file_lines)
    if file_key.startswith("error"):
        _grouped_log_events = map(_parse_error_event, parsed_lines)
        parsed_lines = chain.from_iterable(_grouped_log_events)  # Flatten list of lists

    result = list(parsed_lines)
    print("Got", result)
    return result


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
                logs_from_s3 = _fetch_logs_from_s3(
                    s3_client=s3_client,
                    bucket_name=bucket_name,
                    file_key=file_key,
                )
                yield logs_from_s3

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


def all_logs_are_on_s3(original_logs: list[dict], logs_from_s3: list[dict]):
    return all(log in logs_from_s3 for log in original_logs)
