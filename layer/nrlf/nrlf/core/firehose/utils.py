import base64
import gzip
import json
from typing import Iterator

from aws_lambda_powertools.utilities.parser.models.kinesis_firehose import (
    KinesisFirehoseRecord,
)
from lambda_utils.logging import log_action

from nrlf.core.firehose.log_reference import LogReference
from nrlf.core.validators import json_loads

LOG_SEPARATOR = ""


def load_json_gzip(data: bytes) -> dict:
    return json_loads(gzip.decompress(data))


def dump_json_gzip(obj) -> bytes:
    return gzip.compress(json.dumps(obj).encode())


@log_action(log_reference=LogReference.FIREHOSE007, log_result=True)
def _as_json_stream(items: list[dict]) -> str:
    return LOG_SEPARATOR.join(map(json.dumps, items))


def encode_as_json_stream(items: list[dict], logger=None) -> str:
    return base64.b64encode(
        _as_json_stream(items=items, logger=logger).encode()
    ).decode()


def name_from_arn(arn: str) -> str:
    return arn.split("/")[1]


def list_in_chunks(
    items: list,
    batch_size: int,
) -> Iterator[list]:
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def get_partition_key(record: KinesisFirehoseRecord):
    return (
        record.kinesisRecordMetadata.partitionKey
        if record.kinesisRecordMetadata
        else None
    )
