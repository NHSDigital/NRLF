import json
import warnings

from pydantic import BaseModel
from pytest_mock import MockerFixture

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.decorators import deprecated, error_handler, request_handler
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.response import Response
from nrlf.tests.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
)


def test_error_handler_decorator():
    @error_handler
    def decorated_function():
        return {"message": "Hello, World!"}

    result = decorated_function()
    assert result == {"message": "Hello, World!"}


def test_operation_outcome_error():
    @error_handler
    def decorated_function():
        raise OperationOutcomeError(
            status_code="401",
            severity="error",
            code="unauthorized",
            details=SpineErrorConcept.from_code("AUTHOR_CREDENTIALS_ERROR"),
            diagnostics="The requested DocumentReference cannot be read because it belongs to another organisation",
        )

    result = decorated_function()

    assert result["statusCode"] == "401"
    assert result["headers"] == {}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "unauthorized",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                            "code": "AUTHOR_CREDENTIALS_ERROR",
                            "display": "Author credentials error",
                        }
                    ]
                },
                "diagnostics": "The requested DocumentReference cannot be read because it belongs to another organisation",
            }
        ],
    }


def test_error_handler_decorator_error_handling():
    @error_handler
    def decorated_function():
        raise Exception("Something went wrong")

    result = decorated_function()

    assert result["statusCode"] == "500"
    assert result["headers"] == {}
    assert result["isBase64Encoded"] is False

    # The body is a JSON string, so we need to parse it to compare the contents
    parsed_body = json.loads(result["body"])

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "exception",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                            "code": "INTERNAL_SERVER_ERROR",
                            "display": "Unexpected internal server error",
                        }
                    ]
                },
                "diagnostics": "Something went wrong",
            }
        ],
    }


def test_request_handler_defaults():
    @request_handler()
    def decorated_function() -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(headers=create_headers())
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"message": "Hello, World!"}


def test_request_handler_with_params():
    class MockParams(BaseModel):
        param1: str
        param2: int

    @request_handler(params=MockParams)
    def decorated_function(params) -> Response:
        return Response(
            statusCode="200",
            body=params.json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={"param1": "test", "param2": "123"},
    )

    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"param1": "test", "param2": 123}


def test_request_handler_with_params_missing_params():
    class MockParams(BaseModel):
        param1: str
        param2: int

    @request_handler(params=MockParams)
    def decorated_function(params) -> Response:
        return Response(
            statusCode="200",
            body=params.json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(
        headers=create_headers(), query_string_parameters=None
    )
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "400"
    assert result["headers"] == {}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                            "code": "INVALID_PARAMETER",
                            "display": "Invalid parameter",
                        }
                    ]
                },
                "diagnostics": "Invalid query parameter (param1: field required)",
                "expression": ["param1"],
            },
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                            "code": "INVALID_PARAMETER",
                            "display": "Invalid parameter",
                        }
                    ]
                },
                "diagnostics": "Invalid query parameter (param2: field required)",
                "expression": ["param2"],
            },
        ],
    }


def test_request_handler_with_body():
    class MockBody(BaseModel):
        param1: str
        param2: int

    @request_handler(body=MockBody)
    def decorated_function(event, context, config, metadata, body) -> Response:
        return Response(
            statusCode="200",
            body=body.json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(
        headers=create_headers(), body=json.dumps({"param1": "test", "param2": 123})
    )
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"param1": "test", "param2": 123}


def test_request_handler_with_body_missing_body():
    class MockBody(BaseModel):
        param1: str
        param2: int

    @request_handler(body=MockBody)
    def decorated_function(event, context, config, metadata, body) -> Response:
        return Response(
            statusCode="200",
            body=body.json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(headers=create_headers(), body=None)
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "400"
    assert result["headers"] == {}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                        }
                    ]
                },
                "diagnostics": "Request body is required",
            }
        ],
    }


def test_request_handler_with_body_invalid_body():
    class MockBody(BaseModel):
        param1: str
        param2: int

    @request_handler(body=MockBody)
    def decorated_function(event, context, config, metadata, body) -> Response:
        return Response(
            statusCode="200",
            body=body.json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=json.dumps({"param1": {"invalid": "value"}, "param2": "invalid"}),
    )
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "400"
    assert result["headers"] == {}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])

    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                        }
                    ]
                },
                "diagnostics": "Request body could not be parsed (param1: str type expected)",
                "expression": ["param1"],
            },
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                        }
                    ],
                },
                "diagnostics": "Request body could not be parsed (param2: value is not a valid integer)",
                "expression": ["param2"],
            },
        ],
    }


def test_request_handler_with_request_verification(mocker: MockerFixture):
    parse_headers_mock = mocker.patch("nrlf.core.decorators.parse_headers")

    @request_handler(skip_request_verification=True)
    def decorated_function(event, context) -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event()
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"message": "Hello, World!"}

    assert parse_headers_mock.called is False


def test_request_handler_with_invalid_headers():
    @request_handler()
    def decorated_function(event, context, config, metadata) -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(
        headers={
            "nhsd-connection-metadata": "invalid",
            "nhsd-client-rp-details": "invalid",
        }
    )
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "401"
    assert result["headers"] == {}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {
                    "coding": [
                        {
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                            "code": "MISSING_OR_INVALID_HEADER",
                            "display": "There is a required header missing or invalid",
                        }
                    ]
                },
                "diagnostics": "Unable to parse metadata about the requesting application. Contact the onboarding team.",
            }
        ],
    }


def test_request_handler_with_custom_repository(mocker: MockerFixture):
    repository_mock = mocker.Mock()

    @request_handler(repository=repository_mock)
    def decorated_function(event, context, config, metadata, repository) -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event(headers=create_headers())
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"message": "Hello, World!"}

    repository_mock.assert_called_once()
    assert repository_mock.call_args.kwargs == {
        "environment_prefix": "nrlf",
    }


def test_deprecated_decorator():
    @deprecated("This function is deprecated.")
    def deprecated_function():
        """This function is deprecated."""

    with warnings.catch_warnings(record=True) as warning_list:
        deprecated_function()

        assert len(warning_list) == 1
        assert issubclass(warning_list[0].category, DeprecationWarning)
        assert (
            str(warning_list[0].message)
            == "Call to deprecated function deprecated_function. This function is deprecated."
        )
