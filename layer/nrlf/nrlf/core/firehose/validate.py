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


def _separate_valid_and_invalid_log_events(
    log_events: list[dict], logger: Logger
) -> tuple[list[dict], list[dict]]:
    valid_log_events, invalid_log_events = [], []
    while log_events:
        log_event = log_events.pop(-1)
        try:
            _validate_log_event(log_event=log_event, logger=logger)
        except LogValidationError as err:
            invalid_log_events.append(log_event)
        else:
            valid_log_events.append(log_event)
    return valid_log_events, invalid_log_events


def _determine_outcome_given_record_size(
    valid_outcome_record: FirehoseOutputRecord,
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    total_event_size_bytes: int,
    number_of_logs: int,
    logger: Logger,
):
    try:
        _validate_record_size(
            record_size_bytes=valid_outcome_record.size_bytes,
            total_event_size_bytes=total_event_size_bytes,
            number_of_logs=number_of_logs,
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
        return valid_outcome_record


@log_action(
    narrative="Validating a Cloudwatch Logs record that has been marked as 'DATA_MESSAGE'"
)
def _validate_cloudwatch_logs_data(
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    total_event_size_bytes: int,
    logger: Logger = None,
) -> list[FirehoseOutputRecord]:
    outcome_records = []
    valid_log_events, invalid_log_events = _separate_valid_and_invalid_log_events(
        log_events=cloudwatch_data.log_events, logger=logger
    )

    # Reject invalid parts of the record
    if invalid_log_events:
        outcome_records.append(
            FirehoseOutputRecord(
                record_id=cloudwatch_data.record_id,
                result=FirehoseResult.PROCESSING_FAILED,
            )
        )

    # Keep the valid parts of the record only if pass size requirements
    if valid_log_events:
        _outcome_record = _determine_outcome_given_record_size(
            valid_outcome_record=FirehoseOutputRecord(
                record_id=cloudwatch_data.record_id,
                result=FirehoseResult.OK,
                data=encode_log_events(log_events=valid_log_events),
            ),
            cloudwatch_data=cloudwatch_data,
            partition_key=partition_key,
            total_event_size_bytes=total_event_size_bytes,
            number_of_logs=len(valid_log_events),
            logger=logger,
        )
        outcome_records.append(_outcome_record)

    return outcome_records


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
) -> list[FirehoseOutputRecord]:
    if cloudwatch_data.message_type is CloudwatchMessageType.NORMAL_LOG_EVENT:
        outcome_records = _validate_cloudwatch_logs_data(
            cloudwatch_data=cloudwatch_data,
            partition_key=partition_key,
            total_event_size_bytes=total_event_size_bytes,
            logger=logger,
        )
    else:  # From pydantic validation this must be CloudwatchMessageType.FIREHOSE_HEALTHCHECK_EVENT
        outcome_records = [
            FirehoseOutputRecord(
                record_id=cloudwatch_data.record_id, result=FirehoseResult.DROPPED
            )
        ]
    return outcome_records
