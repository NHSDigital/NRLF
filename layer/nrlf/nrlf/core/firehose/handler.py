from typing import Iterator

from aws_lambda_powertools.utilities.parser.models.kinesis_firehose import (
    KinesisFirehoseModel,
    KinesisFirehoseRecord,
)
from lambda_utils.logging import Logger, log_action
from nrlf.core.firehose.model import (
    CloudwatchLogsData,
    FirehoseOutputRecord,
    FirehoseResult,
    LambdaResult,
)
from nrlf.core.firehose.submission import FirehoseClient, resubmit_unprocessed_records
from nrlf.core.firehose.utils import name_from_arn
from nrlf.core.firehose.validate import process_cloudwatch_record
from pydantic import ValidationError


@log_action(narrative="Processing all Firehose records", log_result=False)
def _process_firehose_records(
    records: list[KinesisFirehoseRecord],
    logger: Logger = None,
) -> Iterator[FirehoseOutputRecord]:
    total_event_size_bytes = 0
    for record in records:
        try:
            cloudwatch_data = CloudwatchLogsData.parse(
                data=record.data, record_id=record.recordId
            )
        except ValidationError:
            yield FirehoseOutputRecord(
                record_id=record.recordId,
                result=FirehoseResult.PROCESSING_FAILED,
            )
        else:
            output_record = process_cloudwatch_record(
                cloudwatch_data=cloudwatch_data,
                partition_key=(
                    record.kinesisRecordMetadata.partitionKey
                    if record.kinesisRecordMetadata
                    else None
                ),
                total_event_size_bytes=total_event_size_bytes,
                logger=logger,
            )
            total_event_size_bytes += output_record.size_bytes
            yield output_record


@log_action(narrative="Executing handler")
def firehose_handler(
    event: KinesisFirehoseModel,
    boto3_firehose_client: any,
    logger: Logger = None,
) -> LambdaResult:
    firehose_client = FirehoseClient(
        client=boto3_firehose_client, stream_name=name_from_arn(event.deliveryStreamArn)
    )

    processed_records = []
    unprocessed_records = []
    for outcome_record in _process_firehose_records(
        records=event.records, logger=logger
    ):
        processed_records.append(outcome_record)
        unprocessed_records += outcome_record.unprocessed_records

    resubmit_unprocessed_records(
        firehose_client=firehose_client,
        unprocessed_records=unprocessed_records,
        logger=logger,
    )

    return LambdaResult(records=processed_records)
