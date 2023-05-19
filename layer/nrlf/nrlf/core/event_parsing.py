from json import JSONDecodeError

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel

from nrlf.core.constants import JSON_TYPES
from nrlf.core.errors import RequestValidationError
from nrlf.core.validators import json_loads


def fetch_body_from_event(event: APIGatewayProxyEventModel) -> dict:
    raw_body = event.body

    try:
        loaded_json = json_loads(raw_body)
    except JSONDecodeError:
        raise RequestValidationError("Body is not valid json")

    if type(loaded_json) not in JSON_TYPES:
        raise RequestValidationError("Body is not expected json type")

    return loaded_json
