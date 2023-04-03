from unittest import mock

import boto3
import pytest
from hypothesis import given
from hypothesis.strategies import builds, just, lists, none
from moto import mock_firehose, mock_s3
from nrlf.core.firehose.model import FirehoseSubmissionRecord
from nrlf.core.firehose.submission import (
    FirehoseClient,
    FirehosePutRecordBatchRequestResponse,
    FirehosePutRecordBatchResponse,
    _submit_records,
    resubmit_unprocessed_records,
)


def raise_test_exception():
    raise _TestException


class _TestException(Exception):
    pass


_NUMBER_RECORDS = 5


@given(records=lists(builds(FirehoseSubmissionRecord), min_size=1))
def test_submit_records_raises_error_after_repeated_client_exceptions(records):
    mocked_firehose_client = mock.Mock()
    mocked_firehose_client.put_record_batch = (
        lambda *args, **kwargs: raise_test_exception()
    )

    firehose_client = FirehoseClient(client=mocked_firehose_client, stream_name="blah")

    with pytest.raises(_TestException):
        _submit_records(
            records=records,
            firehose_client=firehose_client,
        )


@given(
    records=lists(
        builds(FirehoseSubmissionRecord),
        min_size=_NUMBER_RECORDS,
        max_size=_NUMBER_RECORDS,
    ),
    client_response=builds(
        FirehosePutRecordBatchResponse,
        RequestResponses=lists(
            builds(FirehosePutRecordBatchRequestResponse, ErrorCode=just("oops")),
            min_size=_NUMBER_RECORDS,
            max_size=_NUMBER_RECORDS,
        ),
    ),
)
def test_submit_records_raises_error_after_repeated_put_failures(
    records: list[FirehoseSubmissionRecord],
    client_response: FirehosePutRecordBatchResponse,
):
    mocked_firehose_client = mock.Mock()
    mocked_firehose_client.put_record_batch = (
        lambda *args, **kwargs: client_response.dict(by_alias=True)
    )

    firehose_client = FirehoseClient(client=mocked_firehose_client, stream_name="blah")

    with pytest.raises(RuntimeError):
        _submit_records(
            records=records,
            firehose_client=firehose_client,
        )


@given(
    records=lists(
        builds(FirehoseSubmissionRecord),
        min_size=_NUMBER_RECORDS,
        max_size=_NUMBER_RECORDS,
    ),
    client_response=builds(
        FirehosePutRecordBatchResponse,
        RequestResponses=lists(
            builds(FirehosePutRecordBatchRequestResponse, ErrorCode=none()),
            min_size=_NUMBER_RECORDS,
            max_size=_NUMBER_RECORDS,
        ),
    ),
)
def test_submit_records_passes(
    records: list[FirehoseSubmissionRecord],
    client_response: FirehosePutRecordBatchResponse,
):
    mocked_firehose_client = mock.Mock()
    mocked_firehose_client.put_record_batch = (
        lambda *args, **kwargs: client_response.dict(by_alias=True)
    )

    firehose_client = FirehoseClient(client=mocked_firehose_client, stream_name="blah")

    _submit_records(
        records=records,
        firehose_client=firehose_client,
    )


def test_resubmit_unprocessed_records():
    bucket_name = "bucket_name"
    stream_name = "stream_name"

    unprocessed_records = [
        FirehoseSubmissionRecord(Data=b"foo"),
        FirehoseSubmissionRecord(Data=b"bar"),
    ]

    with mock_s3(), mock_firehose():
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=bucket_name)

        firehose_boto3_client = boto3.client("firehose", region_name="us-east-1")
        firehose_boto3_client.create_delivery_stream(
            DeliveryStreamName=stream_name,
            ExtendedS3DestinationConfiguration={
                "RoleARN": "role_arn",
                "BucketARN": bucket_name,
            },
        )

        firehose_client = FirehoseClient(
            client=firehose_boto3_client, stream_name=stream_name
        )

        resubmit_unprocessed_records(
            firehose_client=firehose_client, unprocessed_records=unprocessed_records
        )
