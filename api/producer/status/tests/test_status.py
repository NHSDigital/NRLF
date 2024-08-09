import os

from moto import mock_aws

from api.producer.status.status import handler
from nrlf.tests.dynamodb import mock_repository
from nrlf.tests.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
    default_response_headers,
)


@mock_aws
@mock_repository
def test_status_happy_path(repository):
    event = create_test_api_gateway_event(headers=create_headers())

    result = handler(event, create_mock_context())

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "body": "OK",
        "isBase64Encoded": False,
    }


@mock_aws
@mock_repository
def test_status_unhandled_exception(repository):
    region = os.environ.pop("AWS_REGION")

    event = create_test_api_gateway_event(headers=create_headers())

    result = handler(event, create_mock_context())

    assert result == {
        "statusCode": "503",
        "headers": default_response_headers(),
        "body": "Service unavailable",
        "isBase64Encoded": False,
    }

    os.environ.update(AWS_REGION=region)
