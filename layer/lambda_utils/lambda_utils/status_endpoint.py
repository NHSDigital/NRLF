import os
from contextlib import contextmanager
from enum import Enum
from http import HTTPStatus
from logging import Logger
from types import ModuleType
from typing import Any, Generator

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action, prepare_default_event_for_logging
from lambda_utils.logging_utils import generate_transaction_id
from lambda_utils.pipeline import _execute_steps, _function_handler, _setup_logger
from pydantic import BaseModel

from nrlf.core.model import DocumentPointer
from nrlf.core.repository import Repository


class LogReference(Enum):
    STATUS001 = "Getting environmental variables config"
    STATUS002 = "Getting boto3 client"
    STATUS003 = "Hitting the database"


class Config(BaseModel):
    AWS_REGION: str
    PREFIX: str
    DYNAMODB_TIMEOUT: float


@contextmanager
def get_mutable_pipeline() -> Generator[ModuleType, None, None]:
    from lambda_utils import pipeline

    properties = {k: v for k, v in pipeline.__dict__.items()}
    yield pipeline
    for k, v in properties.items():
        pipeline.__dict__[k] = v


@log_action(log_reference=LogReference.STATUS001, errors_only=True)
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


@log_action(log_reference=LogReference.STATUS003, errors_only=True)
def _hit_the_database(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository = Repository(
        item_type=DocumentPointer,
        client=dependencies["dynamodb_client"],
        environment_prefix=data["config"].PREFIX,
    )
    result = repository.query(pk="D#NULL")
    return PipelineData(result=result)


def _set_missing_logging_headers(event: dict) -> dict:
    headers = event.get("headers", {})
    default_headers = prepare_default_event_for_logging().headers
    default_headers.update(headers)
    return default_headers


def _get_steps(*args, **kwargs):
    return [
        _get_config,
        _hit_the_database,
    ]


def execute_steps(
    index_path: str,
    event: dict,
    context: LambdaContext,
    http_status: HTTPStatus = HTTPStatus.OK,
    initial_pipeline_data={},
    **dependencies,
) -> tuple[HTTPStatus, dict]:
    if context is None:
        context = LambdaContext()

    transaction_id = generate_transaction_id()
    event["headers"] = _set_missing_logging_headers(event=event)
    dependencies["environment"] = os.environ.get("ENVIRONMENT")
    dependencies["splunk_index"] = os.environ.get("SPLUNK_INDEX")
    dependencies["source"] = os.environ.get("SOURCE")

    status_code, response = _function_handler(
        _setup_logger,
        http_status,
        transaction_id=transaction_id,
        args=(index_path, transaction_id, event),
        kwargs=dependencies,
    )
    if status_code is not HTTPStatus.OK:
        return status_code, response
    logger = response

    steps = _get_steps()
    status_code, response = _function_handler(
        _execute_steps,
        http_status,
        transaction_id=transaction_id,
        args=(steps, event, context),
        kwargs={
            "logger": logger,
            "dependencies": dependencies,
            "initial_pipeline_data": initial_pipeline_data,
        },
    )

    if status_code is not HTTPStatus.OK:
        status_code = HTTPStatus.SERVICE_UNAVAILABLE
    return status_code, {"message": status_code.phrase}
