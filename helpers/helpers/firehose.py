import base64
import gzip
import json
from functools import cache
from itertools import chain

from nrlf.core.firehose.utils import load_json_gzip

from helpers.aws_session import new_aws_session


def _parse_error_event(error_event: dict):
    data = load_json_gzip(base64.b64decode(error_event["rawData"]))
    for log in data["logEvents"]:
        msg = log["message"]
        try:
            yield json.loads(msg)
        except:
            yield msg


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
