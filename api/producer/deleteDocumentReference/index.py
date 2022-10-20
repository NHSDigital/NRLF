from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.pipeline import make_pipeline
from lambda_pipeline.types import LambdaContext, PipelineData
from pydantic import ValidationError
from api.producer.deleteDocumentReference.src.config import (
    Config,
    build_persistent_dependencies,
)
from api.producer.deleteDocumentReference.src.v1.handler import steps as v1_steps
from api.producer.deleteDocumentReference.src.v2.handler import steps as v2_steps
from api.producer.deleteDocumentReference.src.versioning import get_version_from_header
from layer.lambda_utils.lambda_utils.versioning import get_steps


config = Config(
    **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
)
dependencies = build_persistent_dependencies(config)


def handler(event: dict, context: LambdaContext = None) -> dict[str, str]:
    if context is None:
        context = LambdaContext()

    status_code, result = execute_steps(event, context, config, **dependencies)
    return render_response(status_code, result)


def execute_steps(event, context, config: Config, **dependencies) -> tuple[int, any]:
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
