import os
from contextlib import contextmanager
from http import HTTPStatus
from logging import Logger
from types import ModuleType
from typing import Any, Generator

import boto3
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.header_config import LoggingHeader
from lambda_utils.logging import log_action, prepare_default_event_for_logging
from lambda_utils.pipeline import render_response
from nrlf.core.constants import NHS_NUMBER_INDEX
from nrlf.core.model import DocumentPointer
from nrlf.core.query import create_search_and_filter_query
from nrlf.core.repository import Repository
from pydantic import BaseModel, ValidationError


class Config(BaseModel):
    AWS_REGION: str
    PREFIX: str


@contextmanager
def get_mutable_pipeline() -> Generator[ModuleType, None, None]:
    from lambda_utils import pipeline

    properties = {k: v for k, v in pipeline.__dict__.items()}
    yield pipeline
    for k, v in properties.items():
        pipeline.__dict__[k] = v


@log_action(narrative="Getting environmental variables config")
def _get_config(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    config = Config(
        **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
    )
    return PipelineData(config=config)


@log_action(narrative="Getting boto3 client", log_result=False)
def _get_boto_client(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    client = boto3.client("dynamodb")
    return PipelineData(client=client, **data)


@log_action(narrative="Hitting the database")
def _hit_the_database(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository = Repository(
        item_type=DocumentPointer,
        client=data["client"],
        environment_prefix=data["config"].PREFIX,
    )
    query = create_search_and_filter_query(nhs_number="NULL")
    result = repository.search(index_name=NHS_NUMBER_INDEX, **query)
    return PipelineData(result=result)


def _get_steps(*args, **kwargs):
    return [
        _get_config,
        _get_boto_client,
        _hit_the_database,
    ]


def _set_missing_logging_headers(event: dict) -> dict:
    headers = event.get("headers", {})
    try:
        LoggingHeader.parse_obj(headers)
    except ValidationError:
        default_headers = prepare_default_event_for_logging().headers
        default_headers.update(headers)
        return default_headers
    else:
        return headers


def handler(event: dict, context: LambdaContext = None) -> dict[str, str]:
    if context is None:
        context = LambdaContext()

    event["headers"] = _set_missing_logging_headers(event=event)

    with get_mutable_pipeline() as mutable_pipeline:
        mutable_pipeline._get_steps_for_version_header = _get_steps
        status_code, result = mutable_pipeline.execute_steps(
            index_path=__file__,
            event=event,
            context=context,
            environment=os.environ.get("ENVIRONMENT"),
        )
    if status_code is not HTTPStatus.OK:
        status_code = HTTPStatus.SERVICE_UNAVAILABLE
    result = {"message": status_code.phrase}

    return render_response(status_code, result)
