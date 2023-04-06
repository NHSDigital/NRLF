import pytest
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_utils.tests.unit.utils import make_aws_event
from nrlf.core.errors import NRLF_TO_SPINE_4XX_ERROR, RequestValidationError
from nrlf.core.event_parsing import fetch_body_from_event


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
    with pytest.raises(RequestValidationError) as e:
        event_model = APIGatewayProxyEventModel(**event)
        fetch_body_from_event(event_model)
    assert str(e.value) == "Body is not valid json"
    assert e.type in NRLF_TO_SPINE_4XX_ERROR
