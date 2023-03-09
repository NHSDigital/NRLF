import base64
import gzip
import json
from typing import Iterator


def load_json_gzip(data: bytes) -> dict:
    return json.loads(gzip.decompress(data))


def _encoded_json_dumps(obj) -> bytes:
    return json.dumps(obj).encode()


def dump_json_gzip(obj) -> bytes:
    return gzip.compress(_encoded_json_dumps(obj))


def encode_log_events(log_events: list[dict]) -> str:
    return base64.b64encode(_encoded_json_dumps(log_events)).decode()


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
