import json
from enum import Enum
from http import HTTPStatus
from pathlib import Path
from types import FunctionType

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.pipeline import make_pipeline
from lambda_pipeline.types import LambdaContext, PipelineData
from lambda_utils.constants import LogLevel
from lambda_utils.logging import (
    Logger,
    MinimalEventModelForLogging,
    log_action,
    prepare_default_event_for_logging,
)
from lambda_utils.logging_utils import generate_transaction_id
from lambda_utils.versioning import (
    get_largest_possible_version,
    get_version_from_header,
    get_versioned_steps,
)
from pydantic import ValidationError

from nrlf.core.response import operation_outcome_not_ok
from nrlf.core.transform import strip_empty_json_paths


class LogReference(Enum):
    OPERATION = "Executing pipeline steps"
    VERSION_CHECK = "Getting version from header"


def _get_steps(
    requested_version: str, versioned_steps: dict[str, FunctionType]
) -> list[FunctionType]:
    version = get_largest_possible_version(
        requested_version, possible_versions=versioned_steps.keys()
    )
    return versioned_steps[version]


def _function_handler(
    fn, status_code_ok: HTTPStatus, transaction_id: str, args, kwargs
) -> tuple[HTTPStatus, any]:
    try:
        status_code, result = status_code_ok, fn(*args, **kwargs)
    except Exception as exception:
        status_code, result = operation_outcome_not_ok(
            transaction_id=transaction_id, exception=exception
        )
    return status_code, result


def _setup_logger(
    index_path: str, transaction_id: str, event: dict, **dependencies
) -> tuple[int, any]:
    try:
        _event = MinimalEventModelForLogging.parse_obj(event)
    except ValidationError:
        _event = prepare_default_event_for_logging()

    lambda_name = Path(index_path).stem
    return Logger(
        logger_name=lambda_name,
        aws_lambda_event=_event,
        aws_environment=dependencies["environment"],
        splunk_index=dependencies["splunk_index"],
        source=dependencies["source"],
        transaction_id=transaction_id,
    )


@log_action(
    log_reference=LogReference.VERSION_CHECK,
    log_level=LogLevel.DEBUG,
    log_fields=["index_path", "event"],
)
def _get_steps_for_version_header(index_path: str, event: dict) -> list[FunctionType]:
    requested_version = get_version_from_header(**event["headers"])
    versioned_steps = get_versioned_steps(index_path)
    return _get_steps(
        requested_version=requested_version, versioned_steps=versioned_steps
    )


@log_action(
    log_reference=LogReference.OPERATION,
    log_level=LogLevel.INFO,
    log_fields=["steps", "event"],
)
def _execute_steps(
    steps: list[FunctionType],
    event: dict,
    context: LambdaContext,
    dependencies: dict,
    logger: Logger,
    initial_pipeline_data={},
) -> dict:
    _event = APIGatewayProxyEventModel(**event)
    pipeline = make_pipeline(
        steps=steps,
        event=_event,
        context=context,
        dependencies=dependencies,
        logger=logger,
    )
    return pipeline(data=PipelineData(**initial_pipeline_data)).to_dict()


def execute_steps(
    index_path: str,
    event: dict,
    context: LambdaContext,
    http_status_ok: HTTPStatus = HTTPStatus.OK,
    initial_pipeline_data={},
    **dependencies,
) -> tuple[HTTPStatus, dict]:
    """
    Executes the handler and wraps it in exception handling
    """
    transaction_id = generate_transaction_id()

    status_code, response = _function_handler(
        _setup_logger,
        status_code_ok=http_status_ok,
        transaction_id=transaction_id,
        args=(index_path, transaction_id, event),
        kwargs=dependencies,
    )

    if status_code is not http_status_ok:
        return status_code, response
    logger = response

    status_code, response = _function_handler(
        _get_steps_for_version_header,
        status_code_ok=http_status_ok,
        transaction_id=transaction_id,
        args=(index_path, event),
        kwargs={"logger": logger},
    )

    if status_code is not http_status_ok:
        return status_code, response
    steps = response

    return _function_handler(
        _execute_steps,
        status_code_ok=http_status_ok,
        transaction_id=transaction_id,
        args=(steps, event, context),
        kwargs={
            "logger": logger,
            "dependencies": dependencies,
            "initial_pipeline_data": initial_pipeline_data,
        },
    )


def render_response(status_code: HTTPStatus, result: dict) -> dict:
    """
    Renders the standard http response envelope
    """
    body = json.dumps(strip_empty_json_paths(result))
    return {
        "statusCode": status_code.value,
        "headers": {"Content-Type": "application/json", "Content-Length": len(body)},
        "body": body,
    }
