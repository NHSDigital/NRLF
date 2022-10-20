import os
from unittest import mock
import pytest

from lambda_utils.tests.unit.utils import make_aws_event, handler_four_hundred


@mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
@pytest.mark.parametrize("event", [(make_aws_event()), (make_aws_event(version="2"))])
def test_handler_returns_200(event: dict):
    import api.producer.readDocumentReference.index as index

    response = index.handler(event)
    assert response["statusCode"] == 200


@mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
@pytest.mark.parametrize("event", [(make_aws_event())])
def test_handler_returns_400(event: dict):
    import api.producer.readDocumentReference.index as index

    index.v1_steps.append(handler_four_hundred)
    response = index.handler(event)
    assert response["statusCode"] == 400


@mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
@pytest.mark.parametrize("event", [(None)])
def test_handler_returns_500(event: dict):
    import api.producer.readDocumentReference.index as index

    response = index.handler(event)
    assert response["statusCode"] == 500
