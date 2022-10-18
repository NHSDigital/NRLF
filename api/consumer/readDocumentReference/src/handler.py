import json

from lambda_pipeline.pipeline import make_pipeline
from lambda_pipeline.types import PipelineData

from aws_lambda_powertools import APIGatewayProxyEventModel
from pydantic import ValidationError
from .v1.handler import steps as v1_steps
from .v2.handler import steps as v2_steps
from .versioning import get_steps, get_version_from_header
from .config import Config


def execute_handler(event, context, config: Config, **dependencies) -> tuple[int, any]:
    """
    Executes the handler and wraps it in exception handling
    """
    try:
        handler_versions = {"1": v1_steps, "2": v2_steps}
        version = get_version_from_header(event)
        steps = get_steps(version, handler_versions)
        pipeline = make_pipeline(
            steps=steps,
            event=APIGatewayProxyEventModel(**event),
            context=context,
            dependencies=dependencies,
        )
        return 200, pipeline(data=PipelineData()).to_dict()
    except ValidationError as e:
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
