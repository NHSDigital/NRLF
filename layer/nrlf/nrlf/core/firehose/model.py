from enum import Enum
from typing import Optional, Union

from nrlf.core.firehose.utils import dump_json_gzip, load_json_gzip
from pydantic import BaseModel, Field, conlist


class FirehoseResult(str, Enum):
    OK = "Ok"
    DROPPED = "Dropped"
    PROCESSING_FAILED = "ProcessingFailed"


class CloudwatchMessageType(str, Enum):
    NORMAL_LOG_EVENT = "DATA_MESSAGE"
    FIREHOSE_HEALTHCHECK_EVENT = "CONTROL_MESSAGE"


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


class CloudwatchLogsData(BaseModel):
    """
    The model for decoded Cloudwatch Logs events received by Kinesis/Firehose.
    One of the few places you can find this schema is casually in the middle of this page:
        https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/SubscriptionFilters.html
    """

    # Fields we need
    record_id: str = Field(exclude=True)  # For convenience, not part of the AWS model
    log_events: conlist(dict, min_items=1) = Field(alias="logEvents")
    message_type: CloudwatchMessageType = Field(alias="messageType")
    # Other fields
    owner: str
    log_group: str = Field(alias="logGroup")
    log_stream: str = Field(alias="logStream")
    subscription_filters: Optional[list[str]] = Field(
        default_factory=list, alias="subscriptionFilters"
    )

    @classmethod
    def parse(cls, data: bytes, record_id: str):
        obj = load_json_gzip(data=data)
        return cls(**obj, record_id=record_id)

    def encode(self) -> bytes:
        return dump_json_gzip(self.dict(by_alias=True))

    def split_in_two(self):
        mid_point = len(self.log_events) // 2
        first_half = self.copy(update={"log_events": self.log_events[:mid_point]})
        second_half = self.copy(update={"log_events": self.log_events[mid_point:]})
        return [first_half, second_half]


class LambdaResult(BaseModel):
    records: conlist(item_type=FirehoseOutputRecord, min_items=1)
