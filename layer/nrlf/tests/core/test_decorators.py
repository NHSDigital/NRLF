import json
import warnings
from typing import Any, Dict, Optional
from unittest.mock import Mock

from pydantic import BaseModel
from pytest_mock import MockerFixture

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.decorators import (
    DYNAMODB_RESOURCE,
    deprecated,
    error_handler,
    request_handler,
)
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.response import Response

_DEFAULT_EVENT_HEADERS = {
    "nhsd-connection-metadata": json.dumps(
        {
            "nrl.pointer-types": [],
            "nrl.ods-code": "X26",
        }
    ),
    "nhsd-client-rp-details": json.dumps(
        {
            "developer.app.name": "TestApp",
            "developer.app.id": "12345",
        }
    ),
}


def create_mock_event(
    query_string_parameters: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = _DEFAULT_EVENT_HEADERS,
    body: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "queryStringParameters": query_string_parameters,
        "headers": headers,
        "body": body,
    }


def create_mock_context() -> Mock:
    return Mock(
        function_name="test_function",
        function_version="1",
        invoked_function_arn="arn:aws:lambda:eu-west-2:123456789012:function:test_function:1",
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
            diagnostics="",
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
                    ],
                    "text": "Author credentials error",
                },
                "diagnostics": "The requested document pointer cannot be read because it belongs to another organisation",
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
                    ],
                    "text": "Unexpected internal server error",
                },
                "diagnostics": "Something went wrong",
            }
        ],
    }


def test_request_handler_defaults():
    @request_handler()
    def decorated_function(event, context, config, metadata) -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_mock_event()
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
    def decorated_function(event, context, config, metadata, params) -> Response:
        return Response(
            statusCode="200",
            body=params.json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_mock_event(
        query_string_parameters={"param1": "test", "param2": "123"}
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
    def decorated_function(event, context, config, metadata, params) -> Response:
        return Response(
            statusCode="200",
            body=params.json(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    event = create_mock_event(query_string_parameters=None)
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
                    ],
                    "text": "Invalid parameter",
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
                    ],
                    "text": "Invalid parameter",
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

    event = create_mock_event(body=json.dumps({"param1": "test", "param2": 123}))
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

    event = create_mock_event(body=None)
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
                    ],
                    "text": "Bad request",
                },
                "diagnostics": "Request body is missing",
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

    event = create_mock_event(
        body=json.dumps({"param1": {"invalid": "value"}, "param2": "invalid"})
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
                    ],
                    "text": "Message not well formed",
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
                    "text": "Message not well formed",
                },
                "diagnostics": "Request body could not be parsed (param2: value is not a valid integer)",
                "expression": ["param2"],
            },
        ],
    }


def test_request_handler_with_skip_parse_headers(mocker: MockerFixture):
    parse_headers_mock = mocker.patch("nrlf.core.decorators.parse_headers")

    @request_handler(skip_parse_headers=True)
    def decorated_function(event, context, config) -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_mock_event()
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

    event = create_mock_event(
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
                    ],
                    "text": "There is a required header missing or invalid",
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

    event = create_mock_event()
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "200"
    assert result["headers"] == {"Content-Type": "application/json"}
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"message": "Hello, World!"}

    repository_mock.assert_called_once()
    assert repository_mock.call_args.kwargs == {
        "dynamodb": DYNAMODB_RESOURCE,
        "environment_prefix": "nrlf",
    }


def test_deprecated_decorator():
    @deprecated("This function is deprecated.")
    def deprecated_function():
        pass

    with warnings.catch_warnings(record=True) as warning_list:
        deprecated_function()

        assert len(warning_list) == 1
        assert issubclass(warning_list[0].category, DeprecationWarning)
        assert (
            str(warning_list[0].message)
            == "Call to deprecated function deprecated_function. This function is deprecated."
        )
