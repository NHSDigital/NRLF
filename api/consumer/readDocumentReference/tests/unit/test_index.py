import os
from unittest import mock
from pydantic import BaseModel, ValidationError, validator
import pytest
from typing import Any

from lambda_utils.tests.unit.utils import make_aws_event
from lambda_pipeline.types import PipelineData, LambdaContext, FrozenDict
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel


class DummyModel(BaseModel):
    foo: bool

    @validator("foo")
    def something(value):
        raise ValueError


def handler_four_hundred(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    DummyModel(foo="1")


@mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
@pytest.mark.parametrize("event", [(make_aws_event()), (make_aws_event(version="2"))])
def test_handler_returns_200(event: dict):
    import api.consumer.readDocumentReference.index as index

    response = index.handler(event)
    assert response["statusCode"] == 200


@mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
@pytest.mark.parametrize("event", [(make_aws_event())])
def test_handler_returns_400(event: dict):
    import api.consumer.readDocumentReference.index as index

    index.v1_steps.append(handler_four_hundred)
    response = index.handler(event)
    assert response["statusCode"] == 400


@mock.patch.dict(os.environ, {"AWS_REGION": "eu-west-2"}, clear=True)
@pytest.mark.parametrize("event", [(None)])
def test_handler_returns_500(event: dict):
    import api.consumer.readDocumentReference.index as index

    response = index.handler(event)
    assert response["statusCode"] == 500
