import json
from functools import cache, wraps
from pathlib import Path
from types import FunctionType

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.pipeline import make_pipeline as _make_pipeline
from lambda_pipeline.types import LambdaContext, PipelineData
from lambda_utils.constants import RUNNING_IN_LOCALSTACK
from lambda_utils.logging import Logger, log_action
from lambda_utils.producer.response import bad_request, get_error_msg
from lambda_utils.versioning import (
    get_largest_possible_version,
    get_version_from_header,
    get_versioned_steps,
)
from nrlf.core.errors import ERROR_SET_4XX
from pydantic import ValidationError


@cache
def __error_set_4xx() -> dict:
    return {exception.__name__: exception for exception in ERROR_SET_4XX}


def _error_set_4xx(name: str) -> Exception:
    return __error_set_4xx().get(name)


def localstack_function_handler(fn):
    """
    LocalStack messes with scope too much to be able to use Python exception
    handling natively. The solution here is to explicitly cast exceptions to the
    class definitions in ERROR_SET_4XX, thus coercing them back into a consistent scope.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as internal_exception:
            exception_name = internal_exception.__class__.__name__
            exception = _error_set_4xx(name=exception_name)
            if exception and exception_name == ValidationError.__name__:
                validation_error = exception(
                    model=internal_exception.model, errors=internal_exception.raw_errors
                )
                validation_error._error_cache = internal_exception.errors()
                raise validation_error
            elif exception:
                raise exception(str(internal_exception))
            raise internal_exception

    return wrapper


def make_pipeline(*args, **kwargs):
    """
    LocalStack messes with scope too much to be able to use the fully decorated
    lambda_pipeline.pipeline.make_pipeline, so instead drop to using the undecorated
    but equivalent _chain_steps. It lacks some validation, but in practice these
    are a development tool rather than a production requirement.
    """
    if RUNNING_IN_LOCALSTACK:
        from lambda_pipeline.pipeline import _chain_steps

        return _chain_steps(*args, **kwargs)
    return _make_pipeline(*args, **kwargs)


def _get_steps(
    requested_version: str, versioned_steps: dict[str, FunctionType]
) -> list[FunctionType]:
    version = get_largest_possible_version(
        requested_version, possible_versions=versioned_steps.keys()
    )
    return versioned_steps[version]


def _function_handler(fn, args, kwargs):
    if RUNNING_IN_LOCALSTACK:
        fn = localstack_function_handler(fn)

    try:
        return 200, fn(*args, **kwargs)
    except ValidationError as e:
        return bad_request(get_error_msg(e))
    except ERROR_SET_4XX as e:
        return bad_request(str(e))
    except Exception as e:
        return 500, {"message": str(e)}


def _setup_logger(index_path: str, event: dict, **dependencies) -> tuple[int, any]:
    _event = APIGatewayProxyEventModel(**event)
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
    initial_pipeline_data={},
) -> tuple[int, any]:
    _event = APIGatewayProxyEventModel(**event)
    pipeline = make_pipeline(
        steps=steps,
        event=_event,
        context=context,
        dependencies=dependencies,
        logger=logger,
    )
    return pipeline(data=PipelineData(**initial_pipeline_data)).to_dict()


def _get_index_path(index_path: str) -> str:
    """
    LocalStack runs the index.py from a different path to the root directory,
    so here we must "reset" the index.py path to root (i.e. chop off the path prefix).
    """
    if RUNNING_IN_LOCALSTACK:
        return Path(index_path).stem
    return index_path


def execute_steps(
    index_path: str,
    event: dict,
    context: LambdaContext,
    initial_pipeline_data={},
    **dependencies
) -> tuple[int, any]:
    """
    Executes the handler and wraps it in exception handling
    """
    index_path = _get_index_path(index_path=index_path)

    status_code, response = _function_handler(
        _setup_logger, args=(index_path, event), kwargs=dependencies
    )

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
