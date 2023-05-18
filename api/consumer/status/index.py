import os

import boto3
from botocore.config import Config
from lambda_utils.pipeline import render_response
from lambda_utils.status_endpoint import execute_steps

_DYNAMODB_TIMEOUT = os.environ.get("DYNAMODB_TIMEOUT")
_AWS_REGION = os.environ.get("AWS_REGION")

DYNAMODB_CLIENT = None
if _AWS_REGION and _DYNAMODB_TIMEOUT:
    DYNAMODB_CLIENT = boto3.client(
        "dynamodb",
        config=Config(read_timeout=float(_DYNAMODB_TIMEOUT), region_name=_AWS_REGION),
    )


def handler(event, context=None) -> dict[str, str]:
    status_code, result = execute_steps(
        index_path=__file__,
        event=event,
        context=context,
        dynamodb_client=DYNAMODB_CLIENT,
    )
    return render_response(status_code, result)
