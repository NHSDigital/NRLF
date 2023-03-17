from enum import Enum


class LogReference(Enum):
    FIREHOSE001 = "Processing all Firehose records"
    FIREHOSE002 = "Executing handler"
    FIREHOSE003 = "Resubmitting unprocessed records to Kinesis/Firehose"
    FIREHOSE004 = (
        "Verifying that size of the processed record is "
        "compatible with the maximum packet size for Kinesis"
    )
    FIREHOSE005 = "Validating that the log structure adheres to the NRLF LogTemplate"
    FIREHOSE006 = "Are all of the provided log events valid?"
    FIREHOSE007 = "Determining Firehose outcome based on the size of this record"
    FIREHOSE008 = (
        "Validating a Cloudwatch Logs record that has been marked as 'DATA_MESSAGE'"
    )
    FIREHOSE009 = (
        "Processing individual Cloudwatch Logs record "
        "(which may contain multiple log entries)"
    )
