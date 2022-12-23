import os
from contextlib import contextmanager
from unittest import mock

import boto3
import moto
import pytest
from lambda_utils.status_endpoint import handler
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


@mock.patch.dict(os.environ, {}, clear=True)
def test_status_fails_if_bad_config(event):
    assert handler(event=event) == SERVICE_UNAVAILABLE


@mock.patch.dict(os.environ, {"PREFIX": ""}, clear=True)
def test_status_fails_if_cant_connect_to_boto(event):
    assert handler(event=event) == SERVICE_UNAVAILABLE


@mock.patch.dict(
    os.environ, {"AWS_DEFAULT_REGION": "eu-west-2", "PREFIX": ""}, clear=True
)
def test_status_fails_if_cant_connect_to_db(event):
    with mock_dynamodb_tables():
        assert handler(event=event) == SERVICE_UNAVAILABLE


@moto.mock_dynamodb
@mock.patch.dict(
    os.environ,
    {"AWS_DEFAULT_REGION": "eu-west-2", "AWS_REGION": "eu-west-2", "PREFIX": ""},
    clear=True,
)
def test_status_ok(event):
    with mock_dynamodb_tables():
        print(handler)
        assert handler(event=event) == OK
