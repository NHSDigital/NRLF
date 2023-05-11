from dataclasses import dataclass
from typing import Optional

from lambda_utils.logging import log_action
from pydantic import BaseModel, Field

from nrlf.core.firehose.log_reference import LogReference
from nrlf.core.firehose.model import FirehoseSubmissionRecord
from nrlf.core.firehose.utils import list_in_chunks

SUBMISSION_BATCH_SIZE = 500
_MAX_SUBMISSION_ATTEMPTS = 20


class FirehosePutRecordBatchRequestResponse(BaseModel):
    """https://docs.aws.amazon.com/firehose/latest/APIReference/API_PutRecordBatchResponseEntry.html"""

    error_code: Optional[str] = Field(alias="ErrorCode", default=None)
    error_message: Optional[str] = Field(alias="ErrorMessage", default=None)
    record_id: Optional[str] = Field(alias="RecordId", default=None)


class FirehosePutRecordBatchResponse(BaseModel):
    """https://docs.aws.amazon.com/firehose/latest/APIReference/API_PutRecordBatch.html"""

    encrypted: bool = Field(alias="Encrypted")
    failed_put_count: int = Field(alias="FailedPutCount")
    request_responses: list[FirehosePutRecordBatchRequestResponse] = Field(
        alias="RequestResponses"
    )


@dataclass
class FirehoseClient:
    client: any
    stream_name: str

    def put(
        self, records: list[FirehoseSubmissionRecord]
    ) -> FirehosePutRecordBatchResponse:
        error = None
        for _ in range(_MAX_SUBMISSION_ATTEMPTS):
            try:
                response = self.client.put_record_batch(
                    DeliveryStreamName=self.stream_name,
                    Records=[record.dict() for record in records],
                )
            except Exception as e:
                error = e
            else:
                return FirehosePutRecordBatchResponse(**response)
        raise error from None


def _submit_records(
    firehose_client: FirehoseClient,
    records: list[FirehoseSubmissionRecord],
    attempts_made=0,
) -> FirehosePutRecordBatchResponse:
    response = firehose_client.put(records=records)

    # Failures can occur somehow even if the client didn't raise an Exception
    # See: https://docs.aws.amazon.com/firehose/latest/APIReference/API_PutRecordBatch.html
    failed_records, error_codes = [], []
    for record, _response in zip(records, response.request_responses):
        if not _response.error_code:
            continue
        error_codes.append(_response.error_code)
        failed_records.append(record)

    if failed_records:
        if attempts_made + 1 >= _MAX_SUBMISSION_ATTEMPTS:
            err_msg = f"Individual error codes: {','.join(error_codes)}"
            raise RuntimeError(
                "Could not put records after %s attempts. %s"
                % (str(attempts_made), err_msg)
            )
        response = _submit_records(
            firehose_client=firehose_client,
            records=failed_records,
            attempts_made=attempts_made + 1,
        )

    return response


@log_action(log_reference=LogReference.FIREHOSE003)
def resubmit_unprocessed_records(
    firehose_client: FirehoseClient,
    unprocessed_records: list[FirehoseSubmissionRecord],
) -> int:
    for records in list_in_chunks(
        items=unprocessed_records, batch_size=SUBMISSION_BATCH_SIZE
    ):
        _submit_records(records=records, firehose_client=firehose_client)
    return len(unprocessed_records)  # Return result for logging purposes
