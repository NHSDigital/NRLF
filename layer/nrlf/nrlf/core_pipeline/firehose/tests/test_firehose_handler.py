import base64
from typing import Union
from unittest import mock

from aws_lambda_powertools.utilities.parser.models.kinesis_firehose import (
    KinesisFirehoseModel,
    KinesisFirehoseRecord,
)
from hypothesis import given
from hypothesis.strategies import DrawFn, builds, composite, just, lists
from lambda_utils.logging import LogData, LogTemplate

from nrlf.core_pipeline.firehose.handler import (
    _process_firehose_records,
    firehose_handler,
)
from nrlf.core_pipeline.firehose.model import (
    CONTROL_MESSAGE_TEXT,
    CloudwatchLogsData,
    CloudwatchMessageType,
    FirehoseOutputRecord,
    FirehoseResult,
    LogEvent,
)
from nrlf.core_pipeline.firehose.validate import MAX_PACKET_SIZE_BYTES
from nrlf.core_pipeline.validators import json_loads


def _log_events_strategy(min_size=1, max_size=None, sensitive=True, message=None):
    if message is None:
        message = just(
            LogTemplate(
                data=LogData(inputs={}, result=""),
                sensitive=sensitive,
                correlation_id="",
                nhsd_correlation_id="",
                request_id="",
                transaction_id="",
                host="",
                index="",
                source="",
                function="",
                environment="",
                log_level="",
                log_reference="",
                outcome="",
                duration_ms=1,
                error="",
                call_stack="",
                timestamp="",
                message="blah",
            ).json()
        )
    return lists(
        builds(
            LogEvent,
            id=just(""),
            timestamp=just(1),
            message=message,
        ),
        min_size=min_size,
        max_size=max_size,
    )


def _cloudwatch_data_strategy(
    message_type,
    min_size=2,
    max_size=None,
    message=None,
    record_id=just(""),
    sensitive=True,
):
    return builds(
        CloudwatchLogsData,
        record_id=record_id,
        messageType=just(message_type),
        logEvents=_log_events_strategy(
            min_size=min_size,
            max_size=max_size,
            message=message,
            sensitive=sensitive,
        ),
        owner=just(""),
        logGroup=just(""),
        logStream=just(""),
        subscription_filters=just([]),
    )


@composite
def bad_cloudwatch_data(draw: DrawFn, logs: list[Union[dict, str]]):
    cloudwatch_data = draw(
        _cloudwatch_data_strategy(
            CloudwatchMessageType.DATA_MESSAGE,
            min_size=len(logs),
            max_size=len(logs),
        )
    ).dict(by_alias=True)
    for i, log in enumerate(logs):
        cloudwatch_data["logEvents"][i]["message"] = log
    return base64.b64encode(CloudwatchLogsData.construct(**cloudwatch_data).encode())


@composite
def _draw_cloudwatch_data(
    draw: DrawFn,
    message_type: str = CloudwatchMessageType.DATA_MESSAGE,
    message: str = None,
    sensitive: bool = True,
    min_size=2,
    max_size=3,
) -> bytes:
    cloudwatch_data = draw(
        _cloudwatch_data_strategy(
            message_type=message_type,
            message=message,
            sensitive=sensitive,
            min_size=min_size,
            max_size=max_size,
        )
    )
    return base64.b64encode(cloudwatch_data.encode())


@given(
    sensitive_records=lists(  # Six sensitive logs (3 x 2)
        builds(
            KinesisFirehoseRecord,
            data=_draw_cloudwatch_data(sensitive=True, min_size=2, max_size=2),
        ),
        min_size=3,
        max_size=3,
    ),
    non_sensitive_records=lists(  # Nine non-sensitive logs (3 x 3)
        builds(
            KinesisFirehoseRecord,
            data=_draw_cloudwatch_data(sensitive=False, min_size=3, max_size=3),
        ),
        min_size=3,
        max_size=3,
    ),
)
def test__process_firehose_records_normal_including_redacted_records(
    sensitive_records: list[KinesisFirehoseRecord],
    non_sensitive_records: list[KinesisFirehoseRecord],
):
    output_records = list(
        _process_firehose_records(records=sensitive_records + non_sensitive_records)
    )
    assert len(output_records) == len(sensitive_records + non_sensitive_records)

    n_lines, n_sensitive, n_not_sensitive = 0, 0, 0
    n_redacted_records = 0
    for record in output_records:
        record_is_sensitive = False

        lines = (
            base64.b64decode(record.data.encode())
            .decode()
            .replace("}{", "}\n{")
            .split("\n")
        )
        for log in map(json_loads, filter(None, lines)):
            n_lines += 1
            if log["event"]["sensitive"]:
                record_is_sensitive = True
                n_sensitive += 1
                assert log["event"]["data"] == "REDACTED"
            else:
                n_not_sensitive += 1
                LogTemplate(**log["event"])
        n_redacted_records += int(record_is_sensitive)

    assert n_lines == 15
    assert n_sensitive == 6
    assert n_not_sensitive == 9
    assert n_redacted_records == len(sensitive_records) == 3


@given(
    good_records=lists(
        builds(
            KinesisFirehoseRecord,
            data=_draw_cloudwatch_data(),
        ),
        min_size=1,
        max_size=1,
    ),
    bad_records=lists(
        builds(
            KinesisFirehoseRecord,
            data=bad_cloudwatch_data(logs=[{"bad": "log"}]),
        ),
        min_size=1,
        max_size=10,
    ),
)
def test__process_firehose_records_normal_records(
    good_records: list[KinesisFirehoseRecord], bad_records: list[KinesisFirehoseRecord]
):
    output_records = list(_process_firehose_records(records=good_records + bad_records))
    total_event_size = sum(
        outcome_record.size_bytes for outcome_record in output_records
    )
    number_of_ok_records = sum(
        outcome_record.result is FirehoseResult.OK for outcome_record in output_records
    )
    number_of_failed_records = sum(
        outcome_record.result is FirehoseResult.PROCESSING_FAILED
        for outcome_record in output_records
    )

    assert len(output_records) == len(good_records + bad_records)
    assert 0 < total_event_size <= MAX_PACKET_SIZE_BYTES
    assert number_of_ok_records == len(good_records)
    assert number_of_failed_records == len(bad_records)


@given(
    good_records=lists(
        builds(
            KinesisFirehoseRecord,
            data=_draw_cloudwatch_data(),
        ),
        min_size=2,
        max_size=4,
    ),
    control_records=lists(
        builds(
            KinesisFirehoseRecord,
            data=_draw_cloudwatch_data(
                message_type=CloudwatchMessageType.CONTROL_MESSAGE,
                message=just(CONTROL_MESSAGE_TEXT),
            ),
        ),
        min_size=1,
        max_size=1,
    ),
)
def test__process_firehose_records_control_records(
    good_records: list[KinesisFirehoseRecord],
    control_records: list[KinesisFirehoseRecord],
):
    output_records = list(
        _process_firehose_records(records=good_records + control_records)
    )
    total_event_size = sum(
        outcome_record.size_bytes for outcome_record in output_records
    )
    number_of_ok_records = sum(
        outcome_record.result is FirehoseResult.OK for outcome_record in output_records
    )
    number_of_dropped_records = sum(
        outcome_record.result is FirehoseResult.DROPPED
        for outcome_record in output_records
    )

    assert len(output_records) == len(good_records + control_records)
    assert 0 < total_event_size <= MAX_PACKET_SIZE_BYTES
    assert number_of_ok_records == len(good_records)
    assert number_of_dropped_records == len(control_records)


@mock.patch("nrlf.core.firehose.handler._process_firehose_records")
@mock.patch("nrlf.core.firehose.handler.resubmit_unprocessed_records")
@given(
    event=builds(
        KinesisFirehoseModel, records=just([]), deliveryStreamArn=just("foo/bar")
    ),
    output_records=lists(builds(FirehoseOutputRecord), min_size=10),
)
def test_firehose_handler(
    event,
    output_records,
    mocked_resubmit_unprocessed_records,
    mocked__process_firehose_records,
):
    mocked__process_firehose_records.return_value = output_records
    result = firehose_handler(
        event=event,
        boto3_firehose_client=None,
    )

    assert result.records == output_records
