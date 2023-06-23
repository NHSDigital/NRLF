from unittest.mock import Mock

import pytest
from hypothesis import given
from hypothesis.strategies import builds, just, lists
from pydantic import ValidationError

from nrlf.core.firehose.model import (
    CONTROL_MESSAGE_TEXT,
    CloudwatchLogsData,
    CloudwatchMessageType,
    FirehoseOutputRecord,
    FirehoseResult,
    FirehoseSubmissionRecord,
    LogEvent,
    parse_cloudwatch_data,
)
from nrlf.core.firehose.tests.test_firehose_handler import _cloudwatch_data_strategy

ENCODED_LOG_EVENTS = "an encoded event"  # Size = 16
RECORD_ID = "123"  # Size = 3


@pytest.mark.parametrize(
    ("firehose_result", "expected_record_size"),
    (
        (FirehoseResult.OK, 19),
        (FirehoseResult.DROPPED, 0),
        (FirehoseResult.PROCESSING_FAILED, 0),
    ),
)
def test_processed_record_size(firehose_result, expected_record_size):
    record = FirehoseOutputRecord(
        record_id=RECORD_ID,
        result=firehose_result,
        data=ENCODED_LOG_EVENTS,
    )
    assert record.size_bytes == expected_record_size


@pytest.mark.parametrize(
    ("firehose_result", "expected_record"),
    (
        (
            FirehoseResult.OK,
            {
                "result": FirehoseResult.OK.value,
                "recordId": RECORD_ID,
                "data": ENCODED_LOG_EVENTS,
            },
        ),
        (
            FirehoseResult.DROPPED,
            {"result": FirehoseResult.DROPPED.value, "recordId": RECORD_ID},
        ),
        (
            FirehoseResult.PROCESSING_FAILED,
            {"result": FirehoseResult.PROCESSING_FAILED.value, "recordId": RECORD_ID},
        ),
    ),
)
@given(unprocessed_records=lists(builds(FirehoseSubmissionRecord)))
def test_processed_record(unprocessed_records, firehose_result, expected_record):
    record = FirehoseOutputRecord(
        record_id=RECORD_ID,
        result=firehose_result,
        data=ENCODED_LOG_EVENTS,
        unprocessed_records=unprocessed_records,
    )
    assert record.dict() == expected_record


@given(cloudwatch_data=_cloudwatch_data_strategy(CloudwatchMessageType.DATA_MESSAGE))
def test_CloudwatchLogsData_split_in_two(cloudwatch_data: CloudwatchLogsData):
    first_half, second_half = cloudwatch_data.split_in_two()
    assert len(first_half.log_events) <= len(second_half.log_events)
    assert first_half.log_events + second_half.log_events == cloudwatch_data.log_events


@given(cloudwatch_data=_cloudwatch_data_strategy(CloudwatchMessageType.DATA_MESSAGE))
def test_parse_cloudwatch_data(cloudwatch_data: CloudwatchLogsData):
    record = Mock()
    record.data = cloudwatch_data.encode()
    record.recordId = cloudwatch_data.record_id
    new_cloudwatch_data = parse_cloudwatch_data(record=record)
    assert new_cloudwatch_data == cloudwatch_data


@pytest.mark.parametrize(
    "message", ["foo", f"foo{CONTROL_MESSAGE_TEXT}bar", CONTROL_MESSAGE_TEXT[1:4]]
)
@given(
    cloudwatch_data=builds(
        CloudwatchLogsData,
        messageType=just(CloudwatchMessageType.CONTROL_MESSAGE),
        logEvents=just([LogEvent(id="", message=CONTROL_MESSAGE_TEXT, timestamp=0)]),
    )
)
def test_control_type_only_works_with_control_message(
    cloudwatch_data: CloudwatchLogsData, message
):
    log_event: LogEvent = cloudwatch_data.log_events[0]
    _log_event = log_event.copy(update={"message": message})
    _cloudwatch_data = cloudwatch_data.copy(update={"logEvents": [_log_event]})
    with pytest.raises(ValidationError):
        CloudwatchLogsData(**_cloudwatch_data.dict())


@given(
    cloudwatch_data=builds(
        CloudwatchLogsData,
        messageType=just(CloudwatchMessageType.CONTROL_MESSAGE),
        logEvents=just([LogEvent(id="", message=CONTROL_MESSAGE_TEXT, timestamp=0)]),
    )
)
def test_control_message_only_works_with_control_type(
    cloudwatch_data: CloudwatchLogsData,
):
    _cloudwatch_data = cloudwatch_data.copy(
        update={"messageType": CloudwatchMessageType.DATA_MESSAGE}
    )
    with pytest.raises(ValidationError):
        CloudwatchLogsData(**_cloudwatch_data.dict())
