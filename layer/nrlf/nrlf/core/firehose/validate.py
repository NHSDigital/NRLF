from lambda_utils.logging import Logger, LogTemplate, log_action
from nrlf.core.firehose.model import (
    CloudwatchLogsData,
    CloudwatchMessageType,
    FirehoseOutputRecord,
    FirehoseResult,
    FirehoseSubmissionRecord,
)
from nrlf.core.firehose.utils import encode_log_events
from pydantic import ValidationError

MAX_PACKET_SIZE_BYTES = (
    6000000  # 6000000 instead of 6291456 to give headroom (according to AWS's example)
)


class RecordTooLargeForKinesis(Exception):
    pass


class RecordTooLargeForKinesisButCanBeSplit(Exception):
    pass


class NoSpaceLeftInCurrentEventPacket(Exception):
    pass


class LogValidationError(Exception):
    pass


@log_action(
    narrative=(
        "Verifying that size of the processed record is "
        "compatible with the maximum packet size for Kinesis"
    )
)
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


@log_action(
    narrative="Validating that the log structure adheres to the NRLF LogTemplate"
)
def _validate_log_event(log_event: dict):
    try:
        log = LogTemplate(**log_event)
    except ValidationError as err:
        raise LogValidationError(str(err))
    if log.dict() != log_event:
        raise LogValidationError("Log has fields that are not present in LogTemplate")


@log_action(narrative="Are all of the provided log events valid?")
def _all_log_events_are_valid(log_events: list[dict], logger: Logger = None) -> bool:
    for log_event in log_events:
        try:
            _validate_log_event(log_event=log_event, logger=logger)
        except LogValidationError:
            return False
    return True


@log_action(narrative="Determining outcome base on the size of this record")
def _determine_outcome_given_record_size(
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    total_event_size_bytes: int,
    logger: Logger = None,
) -> FirehoseOutputRecord:
    output_record = FirehoseOutputRecord(
        record_id=cloudwatch_data.record_id,
        result=FirehoseResult.OK,
        data=encode_log_events(log_events=cloudwatch_data.log_events),
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
                    Data=_record.encode(),
                    PartitionKey=partition_key,
                )
                for _record in cloudwatch_data.split_in_two()
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


@log_action(
    narrative="Validating a Cloudwatch Logs record that has been marked as 'DATA_MESSAGE'",
)
def _validate_cloudwatch_logs_data(
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    total_event_size_bytes: int,
    logger: Logger = None,
) -> FirehoseOutputRecord:

    if not _all_log_events_are_valid(
        log_events=cloudwatch_data.log_events, logger=logger
    ):
        return FirehoseOutputRecord(
            record_id=cloudwatch_data.record_id,
            result=FirehoseResult.PROCESSING_FAILED,
        )

    return _determine_outcome_given_record_size(
        cloudwatch_data=cloudwatch_data,
        partition_key=partition_key,
        total_event_size_bytes=total_event_size_bytes,
        logger=logger,
    )


@log_action(
    narrative=(
        "Processing individual Cloudwatch Logs record "
        "(which may contain multiple log entries)"
    )
)
def process_cloudwatch_record(
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    total_event_size_bytes: int,
    logger: Logger = None,
) -> FirehoseOutputRecord:
    if cloudwatch_data.message_type is CloudwatchMessageType.NORMAL_LOG_EVENT:
        return _validate_cloudwatch_logs_data(
            cloudwatch_data=cloudwatch_data,
            partition_key=partition_key,
            total_event_size_bytes=total_event_size_bytes,
            logger=logger,
        )
    # From pydantic validation this must be CloudwatchMessageType.FIREHOSE_HEALTHCHECK_EVENT
    return FirehoseOutputRecord(
        record_id=cloudwatch_data.record_id, result=FirehoseResult.DROPPED
    )
