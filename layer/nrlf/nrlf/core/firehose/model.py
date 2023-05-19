import json
import time  # noqa: F401
from enum import Enum
from typing import Iterator, Literal, Optional, Union

from aws_lambda_powertools.utilities.parser.models.kinesis_firehose import (
    KinesisFirehoseRecord,
)
from lambda_utils.logging import LogTemplate, log_action
from pydantic import BaseModel, Field, Json, conlist, constr, root_validator

from nrlf.core.firehose.utils import dump_json_gzip, load_json_gzip


class LogReference(Enum):
    FIREHOSEMODEL001 = "Parsing Cloudwatch Logs Event"


class FirehoseResult(str, Enum):
    OK = "Ok"
    DROPPED = "Dropped"
    PROCESSING_FAILED = "ProcessingFailed"


class CloudwatchMessageType(str, Enum):
    DATA_MESSAGE = "DATA_MESSAGE"
    CONTROL_MESSAGE = "CONTROL_MESSAGE"


CONTROL_MESSAGE_TEXT = "CWL CONTROL MESSAGE: Checking health of destination Firehose."


class SplunkEvent(BaseModel):
    """
    The model which Splunk's "collector/event" endpoint expects, as described here:
    https://docs.splunk.com/Documentation/Splunk/latest/Data/FormateventsforHTTPEventCollector
    """

    time: str = Field(default_factory=time.time)
    source: str
    sourcetype: Literal["_json"] = "_json"  # i.e. use the Splunk JSON auto-indexer
    host: str
    event: dict


class FirehoseSubmissionRecord(BaseModel):
    """
    The model which AWS expects for submitting records which cannot be
    processed in this lambda invocation (e.g because the size limit for the
    event packet has been reached)
    """

    Data: bytes
    PartitionKey: Union[str, None] = None

    def dict(self):
        return super().dict(exclude_none=True)


class FirehoseOutputRecord(BaseModel):
    record_id: str
    result: FirehoseResult
    data: str = None
    unprocessed_records: list[FirehoseSubmissionRecord] = Field(
        default_factory=list, exclude=True
    )

    @property
    def size_bytes(self) -> int:
        if self.result is FirehoseResult.OK:
            return len(self.data) + len(self.record_id)
        return 0

    def dict(self, *args, **kwargs):
        data = {"recordId": self.record_id, "result": self.result.value}
        if self.result is FirehoseResult.OK:
            data["data"] = self.data
        return data


class LogEvent(BaseModel):
    id: str
    timestamp: int
    # Read/write to LogTemplate JSON string (see dict method) OR accept the CONTROL_MESSAGE
    message: Union[Json[LogTemplate], constr(regex=f"^{CONTROL_MESSAGE_TEXT}$")]

    def dict(self, *args, **kwargs):
        _dict = super().dict(*args, **kwargs)
        # Pydantic doesn't reserialise to JSON[LogTemplate], so we do so here
        if type(self.message) is LogTemplate:
            _dict["message"] = self.message.json()
        elif type(self.message) in (dict, list):
            _dict["message"] = json.dumps(self.message)
        return _dict


class CloudwatchLogsData(BaseModel):
    """
    The model for decoded Cloudwatch Logs events received by Kinesis/Firehose.
    One of the few places you can find this schema is casually in the middle of this page:
        https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/SubscriptionFilters.html
    """

    # Fields we need
    record_id: str = Field(exclude=True)  # For convenience, not part of the AWS model
    log_events: conlist(item_type=LogEvent, min_items=1) = Field(alias="logEvents")
    message_type: CloudwatchMessageType = Field(alias="messageType")
    # Other fields
    owner: str
    log_group: str = Field(alias="logGroup")
    log_stream: str = Field(alias="logStream")
    subscription_filters: Optional[list[str]] = Field(
        default_factory=list, alias="subscriptionFilters"
    )

    @root_validator
    def validate_control_message_consistency(cls, values):
        log_events: list[LogEvent] = values.get("log_events", [])
        message_type = values.get("message_type")

        is_control_message_type = message_type is CloudwatchMessageType.CONTROL_MESSAGE
        contains_control_message = any(
            log_event.message == CONTROL_MESSAGE_TEXT for log_event in log_events
        )
        if is_control_message_type != contains_control_message:
            raise ValueError(
                f"Message type '{message_type}' not consistent with log events '{log_events}'"
            )
        return values

    def encode(self) -> bytes:
        return dump_json_gzip(self.dict(by_alias=True))

    def split_in_two(self):
        mid_point = len(self.log_events) // 2
        first_half = self.copy(update={"log_events": self.log_events[:mid_point]})
        second_half = self.copy(update={"log_events": self.log_events[mid_point:]})
        return [first_half, second_half]

    @property
    def logs(self) -> Iterator[LogTemplate]:
        for log_event in self.log_events:
            message: LogTemplate = log_event.message
            yield message

    @property
    def redacted_logs(self) -> Iterator[dict]:
        for log_event in self.log_events:
            message: LogTemplate = log_event.message
            yield message.dict(redact=True)


class LambdaResult(BaseModel):
    records: conlist(item_type=FirehoseOutputRecord, min_items=1)


@log_action(log_reference=LogReference.FIREHOSEMODEL001, log_result=True)
def parse_cloudwatch_data(record: KinesisFirehoseRecord) -> CloudwatchLogsData:
    obj = load_json_gzip(data=record.data)
    return CloudwatchLogsData(**obj, record_id=record.recordId)


def format_cloudwatch_logs_for_splunk(
    cloudwatch_data: CloudwatchLogsData,
) -> Iterator[SplunkEvent]:
    yield from (
        SplunkEvent(
            event=redacted_log, source=log.source, host=log.host, index=log.index
        ).dict()
        for log, redacted_log in zip(
            cloudwatch_data.logs, cloudwatch_data.redacted_logs
        )
    )
