import os
from unittest import mock

import boto3
import moto
from behave import fixture

from feature_tests.common.constants import AUTH_STORE, BUCKETS, TABLE_CONFIG
from nrlf.core.types import DynamoDbClient, S3Client


@fixture(name="fixture.mock.dynamodb")
def mock_dynamodb(context, *args, **kwargs):
    with moto.mock_dynamodb():
        yield


@fixture(name="fixture.mock.s3")
def mock_s3(context, *args, **kwargs):
    with moto.mock_s3():
        yield


def setup_tables():
    client: DynamoDbClient = boto3.client("dynamodb")
    for model, config in TABLE_CONFIG.items():
        client.create_table(
            TableName=model.kebab(),
            **config,
        )


def setup_buckets():
    client: S3Client = boto3.client("s3")
    for bucket in BUCKETS:
        client.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={
                "LocationConstraint": "eu-west-2",
            },
        )


@fixture(name="fixture.mock.environmental_variables")
def mock_environmental_variables(context, *args, **kwargs):
    with mock.patch.dict(
        os.environ,
        {
            "AWS_REGION": "eu-west-2",
            "PREFIX": "",
            "DOCUMENT_POINTER_TABLE_NAME": "document-pointer",
            "AWS_DEFAULT_REGION": "eu-west-2",
            "ENVIRONMENT": "__environment__",
            "SPLUNK_INDEX": "__index__",
            "SOURCE": "__source__",
            "DYNAMODB_TIMEOUT": "30",
            "AUTH_STORE": AUTH_STORE,
        },
        clear=True,
    ):
        yield
