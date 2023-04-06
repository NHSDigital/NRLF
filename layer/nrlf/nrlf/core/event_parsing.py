import json

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from nrlf.core.errors import RequestValidationError
from pydantic import BaseModel


def fetch_body_from_event(event: APIGatewayProxyEventModel) -> dict:
    raw_body = event.body
    if isinstance(raw_body, BaseModel):
        return raw_body.dict()

    try:
        if raw_body.isdigit():
            raise RequestValidationError("Body is not valid json")
        return json.loads(raw_body)
    except RequestValidationError as e:
        raise e
    except:
        raise RequestValidationError("Body is not valid json")
