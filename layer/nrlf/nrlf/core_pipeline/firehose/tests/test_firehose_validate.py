from unittest import mock

import pytest
from hypothesis import given
from hypothesis.strategies import data, integers, just, text, tuples

from nrlf.core_pipeline.firehose.model import (
    CONTROL_MESSAGE_TEXT,
    CloudwatchLogsData,
    CloudwatchMessageType,
    FirehoseOutputRecord,
    FirehoseResult,
    FirehoseSubmissionRecord,
)
from nrlf.core_pipeline.firehose.tests.test_firehose_handler import (
    _cloudwatch_data_strategy,
)
from nrlf.core_pipeline.firehose.utils import dump_json_gzip
from nrlf.core_pipeline.firehose.validate import (
    MAX_PACKET_SIZE_BYTES,
    NoSpaceLeftInCurrentEventPacket,
    RecordTooLargeForKinesis,
    RecordTooLargeForKinesisButCanBeSplit,
    _determine_outcome_given_record_size,
    _validate_record_size,
    process_cloudwatch_record,
)


@given(data(), integers())
@pytest.mark.parametrize(
    [
        "record_size_limits",
        "number_of_logs_limits",
        "expected_exception",
    ],
    [
        (
            (MAX_PACKET_SIZE_BYTES, None),
            (1, 1),
            RecordTooLargeForKinesis,
        ),
        (
            (MAX_PACKET_SIZE_BYTES, None),
            (2, None),
            RecordTooLargeForKinesisButCanBeSplit,
        ),
    ],
)
def test__validate_record_size_fails_when_record_too_large(
    record_size_limits,
    number_of_logs_limits,
    expected_exception,
    data,
    event_size,
):
    with pytest.raises(expected_exception):
        _validate_record_size(
            record_size_bytes=data.draw(integers(*record_size_limits)),
            total_event_size_bytes=event_size,
            number_of_logs=data.draw(integers(*number_of_logs_limits)),
        )


@given(
    data=tuples(
        integers(min_value=1, max_value=MAX_PACKET_SIZE_BYTES - 1),
        integers(min_value=0, max_value=2 * MAX_PACKET_SIZE_BYTES),
    ).filter(lambda x: sum(x) >= MAX_PACKET_SIZE_BYTES),
    number_of_logs=integers(min_value=1),
)
def test__validate_record_size_fails_when_total_event_size_is_too_large(
    data, number_of_logs
):
    record_size, event_size = data
    with pytest.raises(NoSpaceLeftInCurrentEventPacket):
        _validate_record_size(
            record_size_bytes=record_size,
            total_event_size_bytes=event_size,
            number_of_logs=number_of_logs,
        )


@given(
    data=tuples(integers(max_value=MAX_PACKET_SIZE_BYTES - 1), integers()).filter(
        lambda x: sum(x) < MAX_PACKET_SIZE_BYTES
    ),
    number_of_logs=integers(min_value=1),
)
def test__validate_record_size_passes(data, number_of_logs):
    record_size, event_size = data
    _validate_record_size(
        record_size_bytes=record_size,
        total_event_size_bytes=event_size,
        number_of_logs=number_of_logs,
    )


def _raise(ex):
    raise ex


@pytest.mark.parametrize(
    ["_validate_record_size_raises", "expected_outcome_record"],
    [
        (
            RecordTooLargeForKinesis,
            FirehoseOutputRecord(
                record_id="record_id",
                result=FirehoseResult.PROCESSING_FAILED,
            ),
        ),
        (
            RecordTooLargeForKinesisButCanBeSplit,
            FirehoseOutputRecord(
                record_id="record_id",
                result=FirehoseResult.DROPPED,
                unprocessed_records=[
                    FirehoseSubmissionRecord(
                        Data=dump_json_gzip(
                            {"recordId": "foo", "logEvents": [{"foo": "FOO"}]}
                        ),
                        PartitionKey="baz",
                    ),
                    FirehoseSubmissionRecord(
                        Data=dump_json_gzip(
                            {"recordId": "foo", "logEvents": [{"bar": "BAR"}]}
                        ),
                        PartitionKey="baz",
                    ),
                ],
            ),
        ),
        (
            NoSpaceLeftInCurrentEventPacket,
            FirehoseOutputRecord(
                record_id="record_id",
                result=FirehoseResult.DROPPED,
                unprocessed_records=[
                    FirehoseSubmissionRecord(
                        Data=dump_json_gzip(
                            {
                                "recordId": "foo",
                                "logEvents": [{"foo": "FOO"}, {"bar": "BAR"}],
                            }
                        ),
                        PartitionKey="baz",
                    )
                ],
            ),
        ),
    ],
)
@mock.patch("nrlf.core.firehose.validate._validate_record_size")
@given(
    cloudwatch_data=_cloudwatch_data_strategy(
        CloudwatchMessageType.DATA_MESSAGE, record_id=just("record_id")
    )
)
def test__determine_outcome_given_record_size(
    _mocked__validate_record_size,
    _validate_record_size_raises,
    expected_outcome_record,
    cloudwatch_data: CloudwatchLogsData,
):
    _mocked__validate_record_size.side_effect = lambda *args, **kwargs: _raise(
        _validate_record_size_raises
    )

    outcome_record = _determine_outcome_given_record_size(
        cloudwatch_data=cloudwatch_data,
        partition_key="baz",
        total_event_size_bytes=None,
        logger=None,
    )

    assert outcome_record == expected_outcome_record


@mock.patch("nrlf.core.firehose.validate._determine_outcome_given_record_size")
def test_process_cloudwatch_record_normal_event(
    mocked__determine_outcome_given_record_size,
):
    cloudwatch_data = mock.Mock()
    cloudwatch_data.message_type = CloudwatchMessageType.DATA_MESSAGE

    return_value = mock.Mock()
    mocked__determine_outcome_given_record_size.return_value = return_value
    assert (
        process_cloudwatch_record(
            cloudwatch_data=cloudwatch_data,
            partition_key=None,
            total_event_size_bytes=None,
        )
        is return_value
    )


@given(
    cloudwatch_data=_cloudwatch_data_strategy(
        message_type=CloudwatchMessageType.CONTROL_MESSAGE,
        message=just(CONTROL_MESSAGE_TEXT),
        min_size=1,
        max_size=1,
    ),
    partition_key=text(),
    total_event_size_bytes=integers(),
)
def test_process_cloudwatch_record_other_event(
    cloudwatch_data: CloudwatchLogsData, partition_key: str, total_event_size_bytes: int
):
    outcome_records = process_cloudwatch_record(
        cloudwatch_data=cloudwatch_data,
        partition_key=partition_key,
        total_event_size_bytes=total_event_size_bytes,
    )
    assert outcome_records == FirehoseOutputRecord(
        record_id=cloudwatch_data.record_id, result=FirehoseResult.DROPPED
    )
