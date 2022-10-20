import os
from unittest import mock
import pytest

from importlib import import_module
from lambda_utils.tests.unit.utils import make_aws_event, handler_four_hundred

ENDPOINTS = [
    "consumer.readDocumentReference",
    "consumer.searchDocumentReference",
    "consumer.searchViaPostDocumentReference",
    "producer.createDocumentReference",
    "producer.deleteDocumentReference",
    "producer.readDocumentReference",
    "producer.searchDocumentReference",
    "producer.updateDocumentReference",
]


@mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
@pytest.mark.parametrize("event", [(make_aws_event()), (make_aws_event(version="2"))])
@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_handler_returns_200(endpoint: str, event: dict):
    index = import_module(f"api.{endpoint}.index")
    response = index.handler(event)
    assert response["statusCode"] == 200


@mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
@mock.patch("lambda_utils.pipeline._get_steps", return_value=[handler_four_hundred])
@pytest.mark.parametrize("event", [(make_aws_event())])
@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_handler_returns_400(mocked__get_steps, endpoint: str, event: dict):
    index = import_module(f"api.{endpoint}.index")
    response = index.handler(event)
    assert response["statusCode"] == 400


@mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
@pytest.mark.parametrize("event", [(None)])
@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_handler_returns_500(endpoint: str, event: dict):
    index = import_module(f"api.{endpoint}.index")
    response = index.handler(event)
    assert response["statusCode"] == 500
