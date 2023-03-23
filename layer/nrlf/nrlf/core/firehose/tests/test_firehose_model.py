import pytest
from hypothesis import given
from hypothesis.strategies import builds, lists
from nrlf.core.firehose.model import (
    CloudwatchLogsData,
    FirehoseOutputRecord,
    FirehoseResult,
    FirehoseSubmissionRecord,
)
from nrlf.core.firehose.tests.test_firehose_handler import draw_log_event

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


@given(
    builds(
        CloudwatchLogsData,
        logEvents=lists(draw_log_event(), min_size=1),
    )
)
def test_CloudwatchLogsData_split_in_two(cloudwatch_data: CloudwatchLogsData):
    first_half, second_half = cloudwatch_data.split_in_two()
    assert len(first_half.log_events) <= len(second_half.log_events)
    assert first_half.log_events + second_half.log_events == cloudwatch_data.log_events


@given(
    builds(
        CloudwatchLogsData,
        logEvents=lists(draw_log_event(), min_size=1),
    )
)
def test_CloudwatchLogsData_parse_and_encode(cloudwatch_data: CloudwatchLogsData):
    cloudwatch_data_encoded = cloudwatch_data.encode()
    new_cloudwatch_data = CloudwatchLogsData.parse(
        data=cloudwatch_data_encoded,
        record_id=cloudwatch_data.record_id,
    )
    assert new_cloudwatch_data == cloudwatch_data
