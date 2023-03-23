import base64
import json
from unittest import mock

import pytest
from aws_lambda_powertools.utilities.parser.models.kinesis_firehose import (
    KinesisFirehoseModel,
    KinesisFirehoseRecord,
)
from hypothesis import given
from hypothesis.strategies import (
    DrawFn,
    builds,
    composite,
    dictionaries,
    just,
    lists,
    sampled_from,
    text,
)
from lambda_utils.logging import LogData, LogTemplate
from nrlf.core.firehose.handler import _process_firehose_records, firehose_handler
from nrlf.core.firehose.model import (
    CloudwatchLogsData,
    CloudwatchMessageType,
    FirehoseOutputRecord,
    FirehoseResult,
    LogEvent,
)
from nrlf.core.firehose.validate import MAX_PACKET_SIZE_BYTES


@composite
def draw_log_message(draw: DrawFn) -> str:
    log = draw(
        builds(
            LogTemplate,
            data=just(LogData(function="foo.bar", inputs={"foo": "bar"}, result="foo")),
            error=just("oops"),
        )
    )
    return log.json()


@composite
def draw_json(draw: DrawFn) -> str:
    log = draw(
        dictionaries(keys=sampled_from(["foo", "bar"]), values=just(""), min_size=1)
    )
    return json.dumps(log)


def draw_log_event(message_strategy=draw_json) -> str:
    return builds(LogEvent, id=just(""), timestamp=just(1), message=message_strategy())


good_logs = lists(
    draw_log_event(message_strategy=draw_log_message),
    min_size=1,
    max_size=20,
)
bad_logs = lists(
    draw_log_event(),
    min_size=1,
    max_size=2,
)


@composite
def _draw_cloudwatch_data(
    draw: DrawFn, logs, message_type: str = CloudwatchMessageType.NORMAL_LOG_EVENT
) -> bytes:
    cloudwatch_data = draw(
        builds(
            CloudwatchLogsData,
            record_id=text(min_size=1),
            logEvents=logs,
            messageType=just(message_type),
        )
    )
    return base64.b64encode(cloudwatch_data.encode())


@pytest.mark.slow
@given(
    good_records=lists(
        builds(
            KinesisFirehoseRecord,
            data=_draw_cloudwatch_data(logs=good_logs),
        ),
        min_size=1,
        max_size=1,
    ),
    bad_records=lists(
        builds(
            KinesisFirehoseRecord,
            data=_draw_cloudwatch_data(logs=bad_logs),
        ),
        min_size=1,
        max_size=10,
    ),
)
def test__process_firehose_records_normal_records(
    good_records: list[KinesisFirehoseRecord], bad_records: list[KinesisFirehoseRecord]
):
    outcome_records = list(
        _process_firehose_records(records=good_records + bad_records)
    )
    total_event_size = sum(
        outcome_record.size_bytes for outcome_record in outcome_records
    )
    number_of_ok_records = sum(
        outcome_record.result is FirehoseResult.OK for outcome_record in outcome_records
    )
    number_of_failed_records = sum(
        outcome_record.result is FirehoseResult.PROCESSING_FAILED
        for outcome_record in outcome_records
    )

    assert len(outcome_records) == len(good_records + bad_records)
    assert 0 < total_event_size <= MAX_PACKET_SIZE_BYTES
    assert number_of_ok_records == len(good_records)
    assert number_of_failed_records == len(bad_records)


@pytest.mark.slow
@given(
    good_records=lists(
        builds(
            KinesisFirehoseRecord,
            data=_draw_cloudwatch_data(logs=good_logs),
        ),
        min_size=1,
        max_size=1,
    ),
    control_records=lists(
        builds(
            KinesisFirehoseRecord,
            data=_draw_cloudwatch_data(
                logs=just(
                    [
                        LogEvent(
                            id="",
                            timestamp=1,
                            message="CWL CONTROL MESSAGE: Checking health of destination Kinesis stream.",
                        )
                    ]
                ),
                message_type=CloudwatchMessageType.FIREHOSE_HEALTHCHECK_EVENT,
            ),
        ),
        min_size=1,
        max_size=10,
    ),
)
def test__process_firehose_records_control_records(
    good_records: list[KinesisFirehoseRecord],
    control_records: list[KinesisFirehoseRecord],
):
    outcome_records = list(
        _process_firehose_records(records=good_records + control_records)
    )
    total_event_size = sum(
        outcome_record.size_bytes for outcome_record in outcome_records
    )
    number_of_ok_records = sum(
        outcome_record.result is FirehoseResult.OK for outcome_record in outcome_records
    )
    number_of_dropped_records = sum(
        outcome_record.result is FirehoseResult.DROPPED
        for outcome_record in outcome_records
    )

    assert len(outcome_records) == len(good_records + control_records)
    assert 0 < total_event_size <= MAX_PACKET_SIZE_BYTES
    assert number_of_ok_records == len(good_records)
    assert number_of_dropped_records == len(control_records)


@mock.patch("nrlf.core.firehose.handler._process_firehose_records")
@mock.patch("nrlf.core.firehose.handler.resubmit_unprocessed_records")
@given(
    event=builds(
        KinesisFirehoseModel, records=just([]), deliveryStreamArn=just("foo/bar")
    ),
    outcome_records=lists(builds(FirehoseOutputRecord), min_size=10),
)
def test_firehose_handler(
    event,
    outcome_records,
    mocked_resubmit_unprocessed_records,
    mocked__process_firehose_records,
):
    mocked__process_firehose_records.return_value = outcome_records
    result = firehose_handler(
        event=event,
        boto3_firehose_client=None,
    )

    assert result.records == outcome_records
