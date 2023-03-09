import os
from unittest import mock

import moto
from lambda_utils.tests.unit.status_test_utils import (
    OK,
    SERVICE_UNAVAILABLE,
    event,
    mock_dynamodb_tables,
)

from api.producer.status.index import handler


@mock.patch.dict(os.environ, {"ENVIRONMENT": ""}, clear=True)
def test_status_fails_if_bad_config(event):
    assert handler(event=event) == SERVICE_UNAVAILABLE


@mock.patch.dict(os.environ, {"ENVIRONMENT": "", "PREFIX": ""}, clear=True)
def test_status_fails_if_cant_connect_to_boto(event):
    assert handler(event=event) == SERVICE_UNAVAILABLE


@mock.patch.dict(
    os.environ,
    {"ENVIRONMENT": "", "AWS_DEFAULT_REGION": "eu-west-2", "PREFIX": ""},
    clear=True,
)
def test_status_fails_if_cant_connect_to_db(event):
    with mock_dynamodb_tables():
        assert handler(event=event) == SERVICE_UNAVAILABLE


@moto.mock_dynamodb
@mock.patch.dict(
    os.environ,
    {
        "ENVIRONMENT": "",
        "AWS_DEFAULT_REGION": "eu-west-2",
        "AWS_REGION": "eu-west-2",
        "PREFIX": "",
    },
    clear=True,
)
def test_status_ok(event):
    with mock_dynamodb_tables():
        assert handler(event=event) == OK
