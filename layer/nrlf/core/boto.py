import functools

import boto3

from nrlf.core.types import DynamoDBServiceResource, S3Client


@functools.cache
def get_boto3_client(service_name: str):
    return boto3.client(service_name)  # type: ignore


@functools.cache
def get_boto3_resource(service_name: str):
    return boto3.resource(service_name)  # type: ignore


def get_dynamodb_resource() -> DynamoDBServiceResource:
    return get_boto3_resource("dynamodb")


@functools.cache
def get_dynamodb_table(table_name: str):
    return get_dynamodb_resource().Table(table_name)


def get_s3_client() -> S3Client:
    return get_boto3_client("s3")
