import os
from unittest import mock

import boto3
import moto
from behave import fixture
from nrlf.core.types import DynamoDbClient

from feature_tests.common.constants import TABLE_CONFIG


@fixture(name="fixture.mock.dynamodb")
def mock_dynamodb(context, *args, **kwargs):
    with moto.mock_dynamodb():
        yield


def setup_tables():
    client: DynamoDbClient = boto3.client("dynamodb")
    for model, config in TABLE_CONFIG.items():
        client.create_table(
            TableName=model.kebab(),
            **config,
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
        },
        clear=True,
    ):
        yield
