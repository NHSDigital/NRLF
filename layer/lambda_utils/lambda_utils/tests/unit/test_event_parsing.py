import pytest
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_utils.errors import RequestParsingError
from lambda_utils.event_parsing import fetch_body_from_event
from lambda_utils.tests.unit.utils import make_aws_event


@pytest.mark.parametrize(
    "event, expected_body",
    [
        (make_aws_event(body='{"test": "test"}'), {"test": "test"}),
        (make_aws_event(body="{}"), {}),
    ],
)
def test_parsing_body_from_event(event, expected_body):
    event_model = APIGatewayProxyEventModel(**event)
    actual_body = fetch_body_from_event(event_model)
    assert actual_body == expected_body


@pytest.mark.parametrize(
    "event",
    [
        make_aws_event(body=None),
        make_aws_event(body=12345),
        make_aws_event(body="12345"),
        make_aws_event(body=True),
    ],
)
def test_parsing_body_from_event_errors(event):
    with pytest.raises(RequestParsingError) as e:
        event_model = APIGatewayProxyEventModel(**event)
        _body = fetch_body_from_event(event_model)
    assert str(e.value) == "Body is not valid json"
