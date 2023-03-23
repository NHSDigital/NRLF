import base64
import gzip
import json
from functools import cache
from itertools import chain

from nrlf.core.firehose.model import CloudwatchLogsData

from helpers.aws_session import new_aws_session


def _parse_error_event(error_event: dict):
    cloudwatch_event = CloudwatchLogsData.parse(
        data=base64.b64decode(error_event["rawData"]), record_id=""
    )
    yield from cloudwatch_event.logs


@cache
def fetch_logs_from_s3(bucket_name, file_key, s3_client=None) -> list[dict]:
    if s3_client is None:
        s3_client = new_aws_session().client("s3")

    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    with gzip.open(response["Body"], "rt") as gf:
        data = gf.read()

    file_lines = filter(bool, data.split("\n"))  # Newline delimited json
    parsed_lines = map(json.loads, file_lines)
    if file_key.startswith("error"):
        _grouped_log_events = map(_parse_error_event, parsed_lines)
        parsed_lines = chain.from_iterable(_grouped_log_events)  # Flatten list of lists

    result = list(parsed_lines)
    return result
