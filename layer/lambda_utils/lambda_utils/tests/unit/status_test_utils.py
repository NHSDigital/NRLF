from contextlib import contextmanager

import boto3
import moto
import pytest
from lambda_utils.tests.unit.utils import make_aws_event

from feature_tests.common.constants import TABLE_CONFIG


@pytest.fixture
def event():
    return make_aws_event(
        headers={
            "x-correlation-id": "123",
            "nhsd-correlation-id": "456",
            "x-request-id": "789",
        }
    )


@contextmanager
def mock_dynamodb_tables():
    with moto.mock_dynamodb():
        client = boto3.client("dynamodb")
        for model, config in TABLE_CONFIG.items():
            client.create_table(
                TableName=model.kebab(),
                **config,
            )
        yield


SERVICE_UNAVAILABLE = {
    "statusCode": 503,
    "headers": {"Content-Type": "application/json", "Content-Length": 34},
    "body": '{"message": "Service Unavailable"}',
}

OK = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json", "Content-Length": 17},
    "body": '{"message": "OK"}',
}
