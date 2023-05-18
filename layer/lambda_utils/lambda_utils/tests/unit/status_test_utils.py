import pytest
from lambda_utils.tests.unit.utils import make_aws_event


@pytest.fixture
def event():
    return make_aws_event(
        headers={
            "x-correlation-id": "123",
            "nhsd-correlation-id": "456",
            "x-request-id": "789",
        }
    )


SERVICE_UNAVAILABLE = {
    "statusCode": 503,
    "headers": {"Content-Type": "application/json", "Content-Length": 34},
    "body": '{"message": "Service Unavailable"}',
}

OK = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json", "Content-Length": 17},
    "body": '{"message": "OK"}',
}

CREATED = {
    "statusCode": 201,
    "headers": {"Content-Type": "application/json", "Content-Length": 17},
    "body": '{"message": "CREATED"}',
}
