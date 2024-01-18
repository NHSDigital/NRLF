import base64
import gzip
import json
import re
from datetime import datetime
from itertools import chain
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4

import boto3
from fire import Fire
from lambda_utils.logging import LogTemplate
from pydantic import BaseModel, Extra, Field, Json, ValidationError, conlist

from helpers.log import log
from nrlf.core.firehose.model import (
    CloudwatchLogsData,
    CloudwatchMessageType,
    FirehoseSubmissionRecord,
    LogEvent,
)
from nrlf.core.firehose.submission import FirehoseClient, _submit_records
from nrlf.core.firehose.utils import load_json_gzip, name_from_arn
from nrlf.core.validators import json_load, json_loads

S3_URI_COMPONENTS = re.compile("^s3://(?P<bucket_name>[^/]+)/(?P<file_key>.*?)$")
DOT_FIREHOSE = ".firehose"
LOCAL_PATH_COMPONENTS = re.compile(
    f"^{DOT_FIREHOSE}/(?P<bucket_name>[^/]+)/(?P<file_key>.*?)$"
)
RESUBMISSION = "cli_resubmission"

ALL_GOOD = "\nAll good ✅"
FAILED_VALIDATION = "\nFailed validation 😞"
NO_ERRORS_FOUND = "No errors found"


class _LogEvent(LogEvent):
    message: Union[Json, str]


class _CloudwatchLogsData(CloudwatchLogsData):
    record_id: None = None
    log_events: conlist(item_type=_LogEvent, min_items=1) = Field(alias="logEvents")


class FirehoseErrorEvent(BaseModel):
    attempts_made: int
    arrival_timestamp: int
    error_code: str
    error_message: str
    attempt_ending_timestamp: int
    raw_data: Union[str, bytes]
    lambda_arn: Optional[str] = None
    event_id: Optional[str] = Field(default=None, alias="EventId")
    subsequence_number: Optional[int] = None

    class Config:
        allow_population_by_field_name = True
        alias_generator = lambda x: "".join(
            word.lower() if i == 0 else word.capitalize()
            for i, word in enumerate(x.split("_"))
        )
        extra = Extra.forbid

    def __str__(self):
        message = [
            "",
            f"\terror_code: {self.error_code}",
            f"\terror_message: {self.error_message}",
        ]

        if self.subsequence_number is not None:
            message.append(f"\tsubsequence_number: {self.subsequence_number}")

        if self.lambda_arn is not None:
            message.append(f"\tlambda_arn: {self.lambda_arn}")

        return "\n".join(message)

    @property
    def cloudwatch_logs_data(self) -> _CloudwatchLogsData:
        data = load_json_gzip(base64.b64decode(self.raw_data))
        return _CloudwatchLogsData(**data)

    @property
    def json_lines(self) -> list[dict]:
        return map(
            json_loads,
            base64.b64decode(self.raw_data).replace(b"}{", b"}\n{").split(b"\n"),
        )


@log("\nError metadata directly from Firehose: {__result__}\n")
def _parse_error_event(error_event: dict):
    return FirehoseErrorEvent(**error_event)


def _get_logs_from_error_event(error_event: dict):
    _error_event = _parse_error_event(error_event=error_event)
    if _error_event.lambda_arn:
        log_events: list[_LogEvent] = _error_event.cloudwatch_logs_data.log_events
        yield from (log_event.message for log_event in log_events)
    else:
        yield from _error_event.json_lines


def _read_gzip_from_s3(s3_client, bucket_name, file_key):
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    with gzip.open(response["Body"], "rt") as gf:
        data = gf.read()
    return data


@log("Retrieved logs from {bucket_name}/{file_key}")
def fetch_logs_from_s3(bucket_name: str, file_key: str, s3_client) -> list[dict]:
    data = _read_gzip_from_s3(
        s3_client=s3_client, bucket_name=bucket_name, file_key=file_key
    )
    file_lines = filter(
        bool, data.replace("}{", "}\n{").split("\n")
    )  # Newline delimited json
    parsed_lines = map(json_loads, file_lines)
    if file_key.startswith("error") or file_key.startswith("fixed"):
        _grouped_log_events = map(_get_logs_from_error_event, parsed_lines)
        parsed_lines = chain.from_iterable(_grouped_log_events)  # Flatten list of lists

    result = list(parsed_lines)
    return result


@log("All logs written to {__result__}")
def _write_s3_logs_to_local(
    s3_path: str, logs: list[dict], local_path=DOT_FIREHOSE
) -> str:
    _path = Path(s3_path.replace("s3:/", local_path))
    _path.parent.mkdir(parents=True, exist_ok=True)
    _path = _path.parent / f"{_path.stem}.json"
    with open(_path, "w") as f:
        json.dump(obj=logs, fp=f)
    return _path


@log("Resubmitted to {stream_arn}")
def submit_cloudwatch_data_to_firehose(
    firehose_client, stream_arn, cloudwatch_data
) -> datetime:
    stream_name = name_from_arn(arn=stream_arn)
    firehose_client = FirehoseClient(client=firehose_client, stream_name=stream_name)

    records = [FirehoseSubmissionRecord(Data=cloudwatch_data.encode())]
    response = _submit_records(firehose_client=firehose_client, records=records)
    assert (
        response.failed_put_count == 0
    ), "Failed to put data to Firehose, this is probably a transient error"
    return datetime.utcnow()


@log("Using stream arn '{__result__}' based on object key")
def _find_stream_arn_on_aws_based_on_file_key(firehose_client, file_key: str):
    response = firehose_client.list_delivery_streams(Limit=100)
    filtered_stream_names = filter(
        lambda stream_name: stream_name in file_key, response["DeliveryStreamNames"]
    )
    try:
        (delivery_stream_name,) = filtered_stream_names
    except ValueError:
        raise ValueError(
            "Could not find exactly one DeliveryStreamName from "
            f"{response['DeliveryStreamNames']} in this environment that matched file {file_key}"
        ) from None

    response = firehose_client.describe_delivery_stream(
        DeliveryStreamName=delivery_stream_name
    )
    return response["DeliveryStreamDescription"]["DeliveryStreamARN"]


@log("Parsed s3 path to {__result__}")
def _parse_s3_uri(s3_path: str):
    re_match = S3_URI_COMPONENTS.match(s3_path)
    if re_match is None:
        raise ValueError(f"'{s3_path}' is not a valid S3 Path ('{S3_URI_COMPONENTS}')")
    return re_match.groupdict()


@log("{__result__}")
def _error_debug_help(path: str):
    return "\n\n".join(
        (
            f"\nYou should now directly amend the file '{path}' so that all "
            "logs are valid. You can validate this file using",
            f"    nrlf firehose validate {path}",
            "and then you can resubmit to Firehose with",
            f"    nrlf firehose resubmit {path} <env>",
        )
    )


def fetch_and_write_logs(s3_path: str, s3_client, local_path=DOT_FIREHOSE):
    path_components = _parse_s3_uri(s3_path=s3_path)
    logs = fetch_logs_from_s3(s3_client=s3_client, **path_components)
    _path = _write_s3_logs_to_local(s3_path=s3_path, logs=logs, local_path=local_path)
    if "error" in s3_path:
        _error_debug_help(path=_path)
    return _path


def _make_timestamp():
    return int(datetime.now().astimezone().timestamp())


@log("Parsed components S3 path components '{__result__}'")
def local_path_to_s3_components(local_path: str) -> dict:
    if not Path(local_path).exists():
        raise FileNotFoundError(local_path)
    re_match = LOCAL_PATH_COMPONENTS.match(local_path)
    if re_match is None:
        raise ValueError(
            f"'{local_path}' is not a valid Local Path ('{LOCAL_PATH_COMPONENTS}')"
        )
    path_components = re_match.groupdict()
    path_components["file_key"] = path_components["file_key"].replace(".json", ".gz")
    return path_components


def validate_logs(logs: list):
    for idx, message in enumerate(logs):
        if type(message) is dict:
            try:
                LogTemplate(**message)
            except ValidationError as validation_error:
                error_msg = "\n".join(
                    f"{err['loc']}  ---  {err['msg']}"
                    for err in validation_error.errors()
                )
                yield {"item_number": idx, "message": error_msg}
        else:
            yield {
                "item_number": idx,
                "message": f"'{message}' is not a valid JSON object.",
            }


@log("{__result__}")
def validate_line_by_line(local_path: str) -> str:
    with open(local_path) as f:
        errors = list(validate_logs(logs=json_load(f)))
    msg = [NO_ERRORS_FOUND]
    if errors:
        msg = ["", f"{len(errors)} errors found in this file"]
        for error in errors:
            msg.append("\nItem number {item_number}:\n{message}".format(**error))

    return "\n".join(msg)


@log("Fully validated and constructed CloudwatchLogsData")
def construct_cloudwatch_logs_data(messages: list[dict]) -> CloudwatchLogsData:
    log_events = [
        LogEvent(
            message=json.dumps(message),
            timestamp=_make_timestamp(),
            id=f"{RESUBMISSION}-str({uuid4()})",
        )
        for message in messages
    ]

    cloudwatch_data = CloudwatchLogsData(  # This line validates the log events
        messageType=CloudwatchMessageType.DATA_MESSAGE,
        logEvents=log_events,
        # Unimportant fields
        record_id="",  # Will be omitted in dict()
        owner=RESUBMISSION,
        logGroup=RESUBMISSION,
        logStream=RESUBMISSION,
    )
    return cloudwatch_data


@log("{__result__}")
def validate(local_path: str):
    local_path_to_s3_components(local_path=local_path)
    msg = validate_line_by_line(local_path=local_path)
    if msg.startswith(NO_ERRORS_FOUND):
        with open(local_path) as f:
            construct_cloudwatch_logs_data(messages=json_load(f))
        return ALL_GOOD
    else:
        return FAILED_VALIDATION


@log("Copied {bucket_name}/{file_key} to {bucket_name}/{__result__}")
def _copy_object(s3_client, bucket_name: str, file_key: str):
    new_key = file_key.replace("errors/", "fixed/")
    s3_client.copy_object(
        Bucket=bucket_name,
        Key=new_key,
        CopySource=f"{bucket_name}/{file_key}",
    )
    return new_key


@log("Deleted {bucket_name}/{file_key}")
def _delete_object(s3_client, bucket_name: str, file_key: str):
    s3_client.delete_object(Bucket=bucket_name, Key=file_key)


@log("Confirmed that {bucket_name}/{file_key} exists")
def _object_exists(s3_client, bucket_name: str, file_key: str):
    s3_client.head_object(Bucket=bucket_name, Key=file_key)


@log("{__result__}")
def resubmit(local_path: str, s3_client, firehose_client):
    # Work out what stream this came from
    path_components = local_path_to_s3_components(local_path=local_path)
    stream_arn = _find_stream_arn_on_aws_based_on_file_key(
        firehose_client=firehose_client, file_key=path_components["file_key"]
    )

    # Double check that we can find the original file on S3
    _object_exists(s3_client=s3_client, **path_components)

    # Validate and resubmit
    msg = validate_line_by_line(local_path=local_path)
    if not msg.startswith(NO_ERRORS_FOUND):
        return FAILED_VALIDATION

    with open(local_path) as f:
        cloudwatch_data = construct_cloudwatch_logs_data(messages=json_load(f))
    submit_cloudwatch_data_to_firehose(
        firehose_client=firehose_client,
        stream_arn=stream_arn,
        cloudwatch_data=cloudwatch_data,
    )
    _copy_object(s3_client=s3_client, **path_components)
    _delete_object(s3_client=s3_client, **path_components)
    return ALL_GOOD


class CLI:
    def __init__(self):
        print("\n-------------------------")  # noqa: T201

    def __del__(self):
        print("-------------------------\n")  # noqa: T201

    def fetch(self, s3_path: str):
        s3_client = boto3.client("s3", region_name="eu-west-2")
        fetch_and_write_logs(s3_path=s3_path, s3_client=s3_client)

    def validate(self, local_path: str):
        validate(local_path=local_path)

    def resubmit(self, local_path: str):
        s3_client = boto3.client("s3", region_name="eu-west-2")
        firehose_client = boto3.client("firehose", region_name="eu-west-2")
        resubmit(
            local_path=local_path, s3_client=s3_client, firehose_client=firehose_client
        )


if __name__ == "__main__":
    Fire(CLI())
