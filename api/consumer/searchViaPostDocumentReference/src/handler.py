import json

from pydantic import ValidationError
from .v1.handler import handler as v1_handler
from .v2.handler import handler as v2_handler
from .versioning import get_handler, get_version_from_header
from .config import Config


def execute_handler(event, config: Config, **dependencies) -> tuple[int, any]:
    """
    Executes the handler and wraps it in exception handling
    """
    try:
        handler_versions = {"1": v1_handler, "2": v2_handler}
        version = get_version_from_header(event)
        handler = get_handler(version, handler_versions)
        return handler(event, config, **dependencies)
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
