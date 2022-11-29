import os

import boto3
from lambda_utils.constants import RUNNING_IN_LOCALSTACK


def boto3_client(*args, **kwargs):
    if RUNNING_IN_LOCALSTACK:
        kwargs = {
            "endpoint_url": f"http://{os.getenv('LOCALSTACK_HOSTNAME')}:{os.getenv('EDGE_PORT')}"
        }
    return boto3.client(*args, **kwargs)
