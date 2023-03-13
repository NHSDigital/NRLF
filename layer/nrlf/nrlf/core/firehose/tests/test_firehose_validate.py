from unittest import mock

import pytest
from hypothesis import given, settings
from hypothesis.strategies import (
    builds,
    data,
    dictionaries,
    integers,
    just,
    lists,
    sampled_from,
    text,
    tuples,
)
from lambda_utils.logging import LogTemplate
from nrlf.core.firehose.model import (
    CloudwatchLogsData,
    CloudwatchMessageType,
    FirehoseOutputRecord,
    FirehoseResult,
    FirehoseSubmissionRecord,
)
from nrlf.core.firehose.utils import dump_json_gzip, encode_log_events
from nrlf.core.firehose.validate import (
    MAX_PACKET_SIZE_BYTES,
    LogValidationError,
    NoSpaceLeftInCurrentEventPacket,
    RecordTooLargeForKinesis,
    RecordTooLargeForKinesisButCanBeSplit,
    _all_log_events_are_valid,
    _determine_outcome_given_record_size,
    _validate_cloudwatch_logs_data,
    _validate_log_event,
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


@given(log_event=builds(LogTemplate))
def test__validate_log_event(log_event: LogTemplate):
    _validate_log_event(log_event=log_event.dict())


@given(
    log_event=builds(LogTemplate),
    extra_fields=dictionaries(keys=text(min_size=1), values=text(), min_size=1),
)
def test__validate_log_event_fails_with_extra_fields(
    log_event: LogTemplate, extra_fields: dict[str, str]
):
    with pytest.raises(LogValidationError):
        _validate_log_event(log_event={**log_event.dict(), **extra_fields})


@given(
    bad_fields=dictionaries(keys=text(min_size=1), values=text(), min_size=0),
)
def test__validate_log_event_fails_with_bad_log_event(bad_fields: dict[str, str]):
    with pytest.raises(LogValidationError):
        _validate_log_event(log_event=bad_fields)


def _raise(ex):
    raise ex


@pytest.mark.slow
@settings(deadline=500)  # In milliseconds
@given(good_log_events=lists(just(True)), bad_log_events=lists(just(False), min_size=1))
@mock.patch("nrlf.core.firehose.validate._validate_log_event")
def test__all_log_events_are_valid(
    mocked__validate_log_event, good_log_events, bad_log_events
):
    mocked__validate_log_event.side_effect = (
        lambda log_event, logger: _raise(LogValidationError) if not log_event else None
    )

    assert (
        _all_log_events_are_valid(
            log_events=good_log_events + bad_log_events, logger=None
        )
        is False
    )


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
    builds(
        CloudwatchLogsData,
        logEvents=just([{"foo": "FOO"}, {"bar": "BAR"}]),
        messageType=just(CloudwatchMessageType.NORMAL_LOG_EVENT),
        record_id=just("record_id"),
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


@mock.patch("nrlf.core.firehose.validate._all_log_events_are_valid", return_value=False)
@given(
    cloudwatch_data=builds(
        CloudwatchLogsData,
        logEvents=lists(dictionaries(keys=text(), values=text()), min_size=2),
    ),
    partition_key=text(),
    total_event_size_bytes=integers(),
)
def test__validate_cloudwatch_logs_record_with_invalid_records(
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    total_event_size_bytes: int,
    mocked__all_log_events_are_valid,
):
    outcome_record = _validate_cloudwatch_logs_data(
        cloudwatch_data=cloudwatch_data,
        partition_key=partition_key,
        total_event_size_bytes=total_event_size_bytes,
    )

    assert outcome_record == FirehoseOutputRecord(
        record_id=cloudwatch_data.record_id,
        result=FirehoseResult.PROCESSING_FAILED,
    )


@mock.patch("nrlf.core.firehose.validate._all_log_events_are_valid", return_value=True)
@given(
    cloudwatch_data=builds(
        CloudwatchLogsData,
        logEvents=lists(dictionaries(keys=text(), values=text()), min_size=1),
    ),
    partition_key=text(),
)
def test__validate_cloudwatch_logs_record_without_invalid_records(
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    mocked__all_log_events_are_valid,
):
    outcome_record = _validate_cloudwatch_logs_data(
        cloudwatch_data=cloudwatch_data,
        partition_key=partition_key,
        total_event_size_bytes=0,
    )

    assert outcome_record == FirehoseOutputRecord(
        record_id=cloudwatch_data.record_id,
        result=FirehoseResult.OK,
        data=encode_log_events(log_events=cloudwatch_data.log_events),
    )


@mock.patch(
    "nrlf.core.firehose.validate._validate_cloudwatch_logs_data", return_value="foo"
)
@given(
    cloudwatch_data=builds(
        CloudwatchLogsData,
        messageType=just(CloudwatchMessageType.NORMAL_LOG_EVENT),
        logEvents=lists(dictionaries(keys=text(), values=text()), min_size=1),
    ),
    partition_key=text(),
    total_event_size_bytes=integers(),
)
def test_process_cloudwatch_record_normal_event(
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    total_event_size_bytes: int,
    mocked__validate_cloudwatch_logs_data,
):
    assert (
        process_cloudwatch_record(
            cloudwatch_data=cloudwatch_data,
            partition_key=partition_key,
            total_event_size_bytes=total_event_size_bytes,
        )
        == "foo"
    )


@given(
    cloudwatch_data=builds(
        CloudwatchLogsData,
        messageType=sampled_from(CloudwatchMessageType).filter(
            lambda x: x is not CloudwatchMessageType.NORMAL_LOG_EVENT
        ),
        logEvents=lists(dictionaries(keys=text(), values=text()), min_size=1),
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
