import json
from types import FunctionType

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.pipeline import make_pipeline
from lambda_pipeline.types import LambdaContext, PipelineData
from pydantic import ValidationError
from nrlf.core.errors import DynamoDbError
from nrlf.core.errors import ItemNotFound

from .versioning import (
    get_largest_possible_version,
    get_version_from_header,
    get_versioned_steps,
)


def _get_steps(
    requested_version: str, versioned_steps: dict[str, FunctionType]
) -> list[FunctionType]:
    version = get_largest_possible_version(
        requested_version, possible_versions=versioned_steps.keys()
    )
    return versioned_steps[version]


def execute_steps(
    index_path: str, event: dict, context: LambdaContext, **dependencies
) -> tuple[int, any]:
    """
    Executes the handler and wraps it in exception handling
    """
    try:
        requested_version = get_version_from_header(event)
        versioned_steps = get_versioned_steps(index_path)
        steps = _get_steps(
            requested_version=requested_version, versioned_steps=versioned_steps
        )
        pipeline = make_pipeline(
            steps=steps,
            event=APIGatewayProxyEventModel(**event),
            context=context,
            dependencies=dependencies,
        )
        return 200, pipeline(data=PipelineData()).to_dict()
    except (ValidationError, ItemNotFound) as e:
        return 400, {"message": str(e)}
    except Exception as e:
        return 500, {"message": str(e)}


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
