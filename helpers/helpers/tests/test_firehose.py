import base64
import gzip
import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import boto3
import pytest
from hypothesis import given, settings
from hypothesis.strategies import builds, dictionaries, integers, just, lists, text
from moto import mock_firehose, mock_s3
from pydantic import ValidationError

from firehose.processor.tests.e2e_utils import _make_good_log
from helpers.firehose import (
    DOT_FIREHOSE,
    _CloudwatchLogsData,
    _error_debug_help,
    _find_stream_arn_on_aws_based_on_file_key,
    _get_logs_from_error_event,
    _LogEvent,
    _parse_error_event,
    _parse_s3_uri,
    _read_gzip_from_s3,
    _write_s3_logs_to_local,
    construct_cloudwatch_logs_data,
    fetch_and_write_logs,
    local_path_to_s3_components,
    validate_logs,
)
from nrlf.core.firehose.model import CloudwatchMessageType
from nrlf.core.validators import json_load, json_loads


@given(
    builds(
        _CloudwatchLogsData,
        logEvents=just([_LogEvent(id="hi", timestamp=1, message="hi")]),
        messageType=just(CloudwatchMessageType.DATA_MESSAGE),
    )
)
def test__parse_error_event(cloudwatch_log_data: _CloudwatchLogsData):
    raw_data = base64.b64encode(cloudwatch_log_data.encode())
    error_event = {
        "attemptsMade": 1,
        "arrivalTimestamp": 123,
        "errorCode": "oops",
        "errorMessage": "oops message",
        "attemptEndingTimestamp": 123,
        "rawData": raw_data,
        "lambdaArn": "oops lambda",
    }
    firehose_error_event = _parse_error_event(error_event=error_event)
    assert firehose_error_event.cloudwatch_logs_data == cloudwatch_log_data
    assert (
        str(firehose_error_event)
        == "\n\terror_code: oops\n\terror_message: oops message\n\tlambda_arn: oops lambda"
    )


@given(
    builds(
        _CloudwatchLogsData,
        logEvents=just([_LogEvent(id="hi", timestamp=1, message="hi")]),
        messageType=just(CloudwatchMessageType.DATA_MESSAGE),
    )
)
def test__get_logs_from_error_event(cloudwatch_log_data: _CloudwatchLogsData):
    raw_data = base64.b64encode(cloudwatch_log_data.encode())
    error_event = {
        "attemptsMade": 1,
        "arrivalTimestamp": 123,
        "errorCode": "oops",
        "errorMessage": "oops message",
        "attemptEndingTimestamp": 123,
        "rawData": raw_data,
        "lambdaArn": "oops",
    }
    logs = list(_get_logs_from_error_event(error_event=error_event))
    assert all(
        log_event.message in logs for log_event in cloudwatch_log_data.log_events
    )


def test__read_gzip_from_s3():
    input_data = "hi"
    body = gzip.compress(input_data.encode())
    with mock_s3():
        s3_client = boto3.client("s3", region_name="eu-west-2")
        s3_client.create_bucket(
            Bucket="bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        s3_client.put_object(Bucket="bucket", Key="FILE_KEY", Body=body)

        data = _read_gzip_from_s3(
            s3_client=s3_client, bucket_name="bucket", file_key="FILE_KEY"
        )
    assert data == input_data


@given(logs=lists(dictionaries(text(), text()), max_size=2))
def test__write_s3_logs_to_local(logs):
    with TemporaryDirectory() as dir:
        _path = _write_s3_logs_to_local(
            s3_path="s3://foo/bar.baz", logs=logs, local_path=dir
        )
        assert _path == Path(dir) / "foo" / "bar.json"
        with open(_path) as f:
            assert json_load(f) == logs


@settings(deadline=3000, max_examples=10)
@given(other_stream_names=lists(text(min_size=5, max_size=5), max_size=99))
def test__find_stream_arn_on_aws_based_on_file_key(other_stream_names):
    mock_firehose_config = {
        "S3DestinationConfiguration": {"RoleARN": "blah", "BucketARN": "blah"},
    }
    target_stream_name = "foo-bar"
    target_file_key = f"blah-blah-{target_stream_name}-blah-blah"
    with mock_firehose():
        firehose_client = boto3.client("firehose")
        firehose_client.create_delivery_stream(
            DeliveryStreamName=target_stream_name, **mock_firehose_config
        )
        for _other_stream_name in set(other_stream_names):
            firehose_client.create_delivery_stream(
                DeliveryStreamName=_other_stream_name, **mock_firehose_config
            )
        stream_arn = _find_stream_arn_on_aws_based_on_file_key(
            firehose_client=firehose_client, file_key=target_file_key
        )
    assert (
        stream_arn
        == f"arn:aws:firehose:eu-west-2:123456789012:deliverystream/{target_stream_name}"
    )


def test__parse_s3_uri():
    assert _parse_s3_uri(s3_path="s3://foo/bar/baz") == {
        "bucket_name": "foo",
        "file_key": "bar/baz",
    }


@contextmanager
def reset_cwd():
    prev_dir = Path.cwd()
    try:
        yield
    finally:
        os.chdir(prev_dir)


def test_local_path_to_s3_components():
    with TemporaryDirectory() as dir:
        local_path = f"{DOT_FIREHOSE}/foo/bar/baz"
        local_full_path = Path(dir) / local_path
        local_full_path.parent.mkdir(parents=True)
        local_full_path.touch()

        with reset_cwd():
            os.chdir(dir)
            local_path_to_s3_components(local_path=local_path) == {
                "bucket_name": "foo",
                "file_key": "bar/baz",
            }


def test__error_debug_help():
    assert type(_error_debug_help(path="path")) is str


@mock.patch("helpers.firehose.fetch_logs_from_s3")
def test_fetch(mocked_fetch_logs_from_s3):
    logs = [{"foo": "bar"}]
    mocked_fetch_logs_from_s3.return_value = logs
    with TemporaryDirectory() as dir:
        _path = fetch_and_write_logs(
            s3_path="s3://foo/bar.baz", s3_client=None, local_path=dir
        )
        assert _path == Path(dir) / "foo" / "bar.json"
        with open(_path) as f:
            assert json_load(f) == logs


@given(
    n_good=integers(min_value=1),
    n_bad=integers(min_value=1),
    n_v_bad=integers(min_value=1),
)
def given__validate_logs(n_good, n_bad, n_v_bad):
    good_logs = [_make_good_log(i) for i in range(n_good)]
    bad_json_logs = [{"value": i} for i in range(n_bad)]
    bad_not_even_json_logs = [f"bad {i}" for i in range(n_v_bad)]

    errors = list(
        validate_logs(logs=good_logs + bad_json_logs + bad_not_even_json_logs)
    )
    assert len(errors) == n_bad + n_v_bad


def test_construct_cloudwatch_logs_data():
    good_logs = [json_loads(_make_good_log(str(i))) for i in range(10)]
    construct_cloudwatch_logs_data(messages=good_logs)


def test_construct_cloudwatch_logs_data_fail():
    with pytest.raises(ValidationError):
        construct_cloudwatch_logs_data(messages=["bad data"])
