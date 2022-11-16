import os

import boto3


def boto3_client(*args, **kwargs):
    if "LOCALSTACK_HOSTNAME" in os.environ:
        kwargs = {
            "endpoint_url": f"http://{os.getenv('LOCALSTACK_HOSTNAME')}:{os.getenv('EDGE_PORT')}"
        }
    return boto3.client(*args, **kwargs)
