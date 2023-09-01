import os
from unittest import mock

import moto
import pytest

from feature_tests.common.fixtures import setup_tables


@pytest.fixture(autouse=True)
def mock_environment():
    with mock.patch.dict(
        os.environ,
        {
            "AWS_REGION": "eu-west-2",
            "AWS_DEFAULT_REGION": "eu-west-2",
            "PREFIX": "",
            "ENVIRONMENT": "",
        },
        clear=True,
    ):
        yield


@pytest.fixture(autouse=True)
def mock_dynamodb():
    with moto.mock_dynamodb():
        setup_tables()
        yield


@mock.patch("cron.seed_sandbox.steps._is_sandbox_lambda", return_value=True)
def test_e2e_local(_mocked__is_sandbox_lambda):
    from cron.seed_sandbox.index import handler

    response = handler(None)
    assert response == {
        "body": '{"message": "ok"}',
        "headers": {"Content-Length": 17, "Content-Type": "application/json"},
        "statusCode": 200,
    }
