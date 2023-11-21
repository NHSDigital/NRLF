from lambda_utils.logging import Logger, log_action

from nrlf.core.firehose.model import (
    CloudwatchLogsData,
    CloudwatchMessageType,
    FirehoseOutputRecord,
    FirehoseResult,
    FirehoseSubmissionRecord,
    format_cloudwatch_logs_for_splunk,
)
from nrlf.core.firehose.utils import encode_as_json_stream
from nrlf.log_references import LogReference

MAX_PACKET_SIZE_BYTES = (
    6000000  # 6000000 instead of 6291456 to give headroom (according to AWS's example)
)


class RecordTooLargeForKinesis(Exception):
    pass


class RecordTooLargeForKinesisButCanBeSplit(Exception):
    pass


class NoSpaceLeftInCurrentEventPacket(Exception):
    pass


@log_action(log_reference=LogReference.FIREHOSE004)
def _validate_record_size(
    record_size_bytes: int,
    total_event_size_bytes: int,
    number_of_logs: int,
):
    if record_size_bytes >= MAX_PACKET_SIZE_BYTES:
        if number_of_logs == 1:
            raise RecordTooLargeForKinesis
        else:
            raise RecordTooLargeForKinesisButCanBeSplit
    elif total_event_size_bytes + record_size_bytes >= MAX_PACKET_SIZE_BYTES:
        raise NoSpaceLeftInCurrentEventPacket


@log_action(log_reference=LogReference.FIREHOSE005, log_result=False)
def _determine_outcome_given_record_size(
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    total_event_size_bytes: int,
    logger: Logger = None,
) -> FirehoseOutputRecord:
    # Unfortunately we have to create the output record this deep into the code
    # since we need to validate the output record size of the encoded logs
    splunk_events = format_cloudwatch_logs_for_splunk(cloudwatch_data=cloudwatch_data)
    output_record = FirehoseOutputRecord(
        record_id=cloudwatch_data.record_id,
        result=FirehoseResult.OK,
        data=encode_as_json_stream(items=splunk_events, logger=logger),
    )

    try:
        _validate_record_size(
            record_size_bytes=output_record.size_bytes,
            total_event_size_bytes=total_event_size_bytes,
            number_of_logs=len(cloudwatch_data.log_events),
            logger=logger,
        )
    except RecordTooLargeForKinesis:
        # This record will never fit in the packet, so reject
        return FirehoseOutputRecord(
            record_id=cloudwatch_data.record_id,
            result=FirehoseResult.PROCESSING_FAILED,
        )
    except RecordTooLargeForKinesisButCanBeSplit:
        # Split this record in two then save for later, as there is no space in this packet
        return FirehoseOutputRecord(
            record_id=cloudwatch_data.record_id,
            result=FirehoseResult.DROPPED,
            unprocessed_records=[
                FirehoseSubmissionRecord(
                    Data=_cloudwatch_data.encode(),
                    PartitionKey=partition_key,
                )
                for _cloudwatch_data in cloudwatch_data.split_in_two()
            ],
        )
    except NoSpaceLeftInCurrentEventPacket:
        # Save this record for later, as there is no space in this packet
        return FirehoseOutputRecord(
            record_id=cloudwatch_data.record_id,
            result=FirehoseResult.DROPPED,
            unprocessed_records=[
                FirehoseSubmissionRecord(
                    Data=cloudwatch_data.encode(), PartitionKey=partition_key
                )
            ],
        )
    else:  # Default case: this record passes the validation
        return output_record


@log_action(log_reference=LogReference.FIREHOSE006, log_result=False)
def process_cloudwatch_record(
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    total_event_size_bytes: int,
    logger: Logger = None,
) -> FirehoseOutputRecord:
    if cloudwatch_data.message_type is CloudwatchMessageType.DATA_MESSAGE:
        return _determine_outcome_given_record_size(
            cloudwatch_data=cloudwatch_data,
            partition_key=partition_key,
            total_event_size_bytes=total_event_size_bytes,
            logger=logger,
        )
    # From pydantic validation this must be CloudwatchMessageType.CONTROL_MESSAGE
    return FirehoseOutputRecord(
        record_id=cloudwatch_data.record_id, result=FirehoseResult.DROPPED
    )
