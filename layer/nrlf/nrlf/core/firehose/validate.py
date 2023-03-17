from lambda_utils.logging import Logger, LogTemplate, log_action
from nrlf.core.firehose.log_reference import LogReference
from nrlf.core.firehose.model import (
    CloudwatchLogsData,
    CloudwatchMessageType,
    FirehoseOutputRecord,
    FirehoseResult,
    FirehoseSubmissionRecord,
)
from nrlf.core.firehose.utils import encode_logs_as_ndjson
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


@log_action(log_reference=LogReference.FIREHOSE005, log_fields=["log"])
def _validate_log(log: dict):
    try:
        parsed_log = LogTemplate(**log)
    except ValidationError as err:
        raise LogValidationError(str(err))
    rendered_log = parsed_log.dict()
    if rendered_log != log:
        raise LogValidationError(
            f"Field mismatch between parsed and proved logs. Parsed log: {rendered_log}"
        )


@log_action(log_reference=LogReference.FIREHOSE006)
def _all_logs_are_valid(logs: list[dict], logger: Logger = None) -> bool:
    for log in logs:
        try:
            _validate_log(log=log, logger=logger)
        except LogValidationError:
            return False
    return True


@log_action(log_reference=LogReference.FIREHOSE007, log_result=False)
def _determine_outcome_given_record_size(
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    total_event_size_bytes: int,
    logger: Logger = None,
) -> FirehoseOutputRecord:
    output_record = FirehoseOutputRecord(
        record_id=cloudwatch_data.record_id,
        result=FirehoseResult.OK,
        data=encode_logs_as_ndjson(logs=cloudwatch_data.logs),
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


@log_action(log_reference=LogReference.FIREHOSE008, log_result=False)
def _validate_cloudwatch_logs_data(
    cloudwatch_data: CloudwatchLogsData,
    partition_key: str,
    total_event_size_bytes: int,
    logger: Logger = None,
) -> FirehoseOutputRecord:

    if not _all_logs_are_valid(logs=cloudwatch_data.logs, logger=logger):
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


@log_action(log_reference=LogReference.FIREHOSE009, log_result=False)
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
