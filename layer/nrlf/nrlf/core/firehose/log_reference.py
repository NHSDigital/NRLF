from enum import Enum


class LogReference(Enum):
    FIREHOSE001 = "Processing all Firehose records"
    FIREHOSE002 = "Executing handler"
    FIREHOSE003 = "Resubmitting unprocessed records to Kinesis/Firehose"
    FIREHOSE004 = (
        "Verifying that size of the processed record is "
        "compatible with the maximum packet size for Kinesis"
    )
    FIREHOSE005 = "Determining Firehose outcome based on the size of this record"
    FIREHOSE006 = (
        "Processing individual Cloudwatch Logs record "
        "(which may contain multiple log entries)"
    )
    FIREHOSE007 = "Joining Splunk logs"
