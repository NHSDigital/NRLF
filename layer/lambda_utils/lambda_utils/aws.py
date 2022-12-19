import boto3


def boto3_client(*args, **kwargs):
    return boto3.client(*args, **kwargs)
