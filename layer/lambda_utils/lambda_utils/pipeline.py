import json
from pathlib import Path
from types import FunctionType

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.pipeline import make_pipeline
from lambda_pipeline.types import LambdaContext, PipelineData
from lambda_utils.logging import Logger, log_action
from lambda_utils.producer.response import bad_request, get_error_msg
from lambda_utils.versioning import (
    get_largest_possible_version,
    get_version_from_header,
    get_versioned_steps,
)
from nrlf.core.errors import ERROR_SET_4XX
from pydantic import ValidationError


def _get_steps(
    requested_version: str, versioned_steps: dict[str, FunctionType]
) -> list[FunctionType]:
    version = get_largest_possible_version(
        requested_version, possible_versions=versioned_steps.keys()
    )
    return versioned_steps[version]


def _function_handler(fn, args, kwargs):
    try:
        return 200, fn(*args, **kwargs)
    except ValidationError as e:
        return bad_request(get_error_msg(e))
    except ERROR_SET_4XX as e:
        return bad_request(str(e))
    except Exception as e:
        return 500, {"message": str(e)}


def _setup_logger(
    index_path: str, event: dict, extra_event_kwargs: dict, **dependencies
) -> tuple[int, any]:
    _event = APIGatewayProxyEventModel(**event, **extra_event_kwargs)
    lambda_name = Path(index_path).stem
    return Logger(
        logger_name=lambda_name,
        aws_lambda_event=_event,
        aws_environment=dependencies["environment"],
    )


@log_action(narrative="Getting version from header", log_fields=["index_path", "event"])
def _get_steps_for_version_header(index_path: str, event: dict) -> tuple[int, any]:
    requested_version = get_version_from_header(event)
    versioned_steps = get_versioned_steps(index_path)
    return _get_steps(
        requested_version=requested_version, versioned_steps=versioned_steps
    )


@log_action(narrative="Executing pipeline steps", log_fields=["steps", "event"])
def _execute_steps(
    steps: list[FunctionType],
    event: dict,
    context: LambdaContext,
    dependencies: dict,
    logger: Logger,
    extra_event_kwargs={},
    initial_pipeline_data={},
) -> tuple[int, any]:
    _event = APIGatewayProxyEventModel(**event, **extra_event_kwargs)
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
    extra_event_kwargs={},
    initial_pipeline_data={},
    **dependencies
) -> tuple[int, any]:
    """
    Executes the handler and wraps it in exception handling
    """
    print("here?")
    status_code, response = _function_handler(
        _setup_logger, args=(index_path, event, extra_event_kwargs), kwargs=dependencies
    )
    print("here?2", response)

    if status_code != 200:
        return status_code, response
    logger = response

    status_code, response = _function_handler(
        _get_steps_for_version_header,
        args=(index_path, event),
        kwargs={"logger": logger},
    )

    if status_code != 200:
        return status_code, response
    steps = response

    return _function_handler(
        _execute_steps,
        args=(steps, event, context),
        kwargs={
            "logger": logger,
            "dependencies": dependencies,
            "initial_pipeline_data": initial_pipeline_data,
            "extra_event_kwargs": extra_event_kwargs,
        },
    )


def render_response(status_code: int, result: any) -> dict:
    """
    Renders the standard http response envelope
    """
    body = json.dumps(result)
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Content-Length": len(body)},
        "body": body,
    }
