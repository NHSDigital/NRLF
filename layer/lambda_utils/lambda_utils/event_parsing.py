import json

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_utils.errors import RequestParsingError
from pydantic import BaseModel


def fetch_body_from_event(event: APIGatewayProxyEventModel) -> dict:
    raw_body = event.body
    if isinstance(raw_body, BaseModel):
        return raw_body.dict()

    try:
        if raw_body.isdigit():
            raise RequestParsingError("Body is not valid json")
        return json.loads(raw_body)
    except RequestParsingError as e:
        raise e
    except:
        raise RequestParsingError("Body is not valid json")
