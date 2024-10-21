import json
import warnings

import pytest
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from pydantic import BaseModel
from pytest_mock import MockerFixture

from nrlf.core.authoriser import parse_permissions_file
from nrlf.core.codes import SpineErrorConcept
from nrlf.core.config import Config
from nrlf.core.constants import (
    PERMISSION_ALLOW_ALL_POINTER_TYPES,
    X_REQUEST_ID_HEADER,
    PointerTypes,
)
from nrlf.core.decorators import (
    deprecated,
    error_handler,
    header_handler,
    load_connection_metadata,
    logger_initialiser,
    request_handler,
    verify_request_ids,
)
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import LogReference
from nrlf.core.request import parse_headers
from nrlf.core.response import Response
from nrlf.tests.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
    default_response_headers,
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


def test_header_handler_happy_path():
    @header_handler
    def decorated_function(event):
        return {
            "headers": {
                "Content-Type": "application/json",
            }
        }

    test_event = create_test_api_gateway_event()
    event = APIGatewayProxyEvent(test_event)

    response = decorated_function(event)

    assert response["headers"] == {
        **default_response_headers(),
        "Content-Type": "application/json",
    }


def test_header_handler_when_correlation_id_is_also_present():
    @header_handler
    def decorated_function(event):
        return {
            "headers": {
                "Content-Type": "application/json",
            }
        }

    test_event = create_test_api_gateway_event(
        headers={
            **create_headers(),
            "X-Correlation-Id": "test_correlation_id",
        }
    )
    event = APIGatewayProxyEvent(test_event)

    response = decorated_function(event)

    assert response["headers"] == {
        **default_response_headers(),
        "Content-Type": "application/json",
        "X-Correlation-Id": "test_correlation_id",
    }


def test_header_handler_when_no_response_headers():
    @header_handler
    def decorated_function(event):
        return {}

    test_event = create_test_api_gateway_event()
    event = APIGatewayProxyEvent(test_event)

    response = decorated_function(event)

    assert response["headers"] == default_response_headers()


def test_header_handler_when_no_echoed_headers():
    @header_handler
    def decorated_function(event):
        return {
            "headers": {
                "Content-Type": "application/json",
            }
        }

    test_event = create_test_api_gateway_event(headers={"X-None-Echoed-Header": "test"})
    event = APIGatewayProxyEvent(test_event)

    response = decorated_function(event)

    assert response["headers"] == {
        "Content-Type": "application/json",
    }


def test_header_handler_with_overwritten_response_headers():
    @header_handler
    def decorated_function(event):
        return {
            "headers": {
                "Content-Type": "application/json",
                "X-Request-Id": "test_request_id_overwrite_me",
                "X-Correlation-Id": "test_correlation_id_overwrite_me",
            }
        }

    test_event = create_test_api_gateway_event(
        headers={
            **create_headers(),
            "X-Correlation-Id": "test_correlation_id",
        }
    )
    event = APIGatewayProxyEvent(test_event)

    response = decorated_function(event)

    assert response["headers"] == {
        "Content-Type": "application/json",
        "X-Request-Id": "test_request_id",
        "X-Correlation-Id": "test_correlation_id",
    }


def test_header_handler_when_response_header_checks_fail(mocker: MockerFixture):
    @header_handler
    def decorated_function(event):
        return {
            "headers": {
                "Content-Type": "application/json",
                "X-Request-Id": "test_request_id_not_overwritten",
                "X-Correlation-Id": "test_correlation_id_not_overwritten",
            }
        }

    event = mocker.MagicMock()
    event.get_header_value.side_effect = Exception("Test exception")

    response = decorated_function(event)

    assert response["headers"] == {
        "Content-Type": "application/json",
        "X-Request-Id": "test_request_id_not_overwritten",
        "X-Correlation-Id": "test_correlation_id_not_overwritten",
    }


def test_logger_initialiser_happy_path(mocker: MockerFixture):
    mock_logger = mocker.patch("nrlf.core.decorators.logger")

    @logger_initialiser
    def decorated_function(event):
        return {}

    test_event = create_test_api_gateway_event()
    event = APIGatewayProxyEvent(test_event)

    decorated_function(event)

    mock_logger.set_correlation_id.assert_called_once_with("test_correlation_id")


def test_logger_initialiser_no_correlation_id(mocker: MockerFixture):
    mock_logger = mocker.patch("nrlf.core.decorators.logger")

    @logger_initialiser
    def decorated_function(event):
        return {}

    test_event = create_test_api_gateway_event(
        headers={
            **create_headers(),
            "NHSD-Correlation-Id": None,
        }
    )
    event = APIGatewayProxyEvent(test_event)

    decorated_function(event)

    mock_logger.set_correlation_id.assert_not_called()
    mock_logger.log.assert_called_once_with(
        LogReference.HANDLER017,
        id_header="NHSD-Correlation-Id",
        headers=test_event["headers"],
    )


def test_verify_request_id_happy_path():
    test_event = create_test_api_gateway_event()

    event = APIGatewayProxyEvent(test_event)
    verify_request_ids(event)


def test_verify_request_id_no_request_id():
    test_event = create_test_api_gateway_event()
    test_event["headers"].pop(X_REQUEST_ID_HEADER)

    event = APIGatewayProxyEvent(test_event)
    with pytest.raises(OperationOutcomeError) as err:
        verify_request_ids(event)

    assert err.value.status_code == "400"
    assert err.value.operation_outcome.resourceType == "OperationOutcome"
    assert err.value.operation_outcome.issue[0].severity == "error"
    assert err.value.operation_outcome.issue[0].code == "invalid"
    assert err.value.operation_outcome.issue[0].details == SpineErrorConcept.from_code(
        "MISSING_OR_INVALID_HEADER"
    )
    assert (
        err.value.operation_outcome.issue[0].diagnostics
        == "The X-Request-Id header is missing or invalid"
    )
    assert err.value.operation_outcome.issue[0].expression == None


def test_verify_request_id_no_correlation_id():
    test_event = create_test_api_gateway_event()
    test_event["headers"].pop("NHSD-Correlation-Id")

    event = APIGatewayProxyEvent(test_event)
    with pytest.raises(OperationOutcomeError) as err:
        verify_request_ids(event)

    assert err.value.status_code == "400"
    assert err.value.operation_outcome.resourceType == "OperationOutcome"
    assert err.value.operation_outcome.issue[0].severity == "error"
    assert err.value.operation_outcome.issue[0].code == "invalid"
    assert err.value.operation_outcome.issue[0].details == SpineErrorConcept.from_code(
        "MISSING_OR_INVALID_HEADER"
    )
    assert (
        err.value.operation_outcome.issue[0].diagnostics
        == "The NHSD-Correlation-Id header is missing or invalid"
    )
    assert err.value.operation_outcome.issue[0].expression == None


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
    assert result["headers"] == {
        "Content-Type": "application/json",
        **default_response_headers(),
    }
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
    assert result["headers"] == {
        "Content-Type": "application/json",
        **default_response_headers(),
    }
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
    assert result["headers"] == default_response_headers()
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
                "diagnostics": "Invalid query parameter (param1: Field required)",
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
                "diagnostics": "Invalid query parameter (param2: Field required)",
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
    assert result["headers"] == {
        "Content-Type": "application/json",
        **default_response_headers(),
    }
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
    assert result["headers"] == default_response_headers()
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
    assert result["headers"] == default_response_headers()
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
    assert result["headers"] == {
        "Content-Type": "application/json",
        **default_response_headers(),
    }
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"message": "Hello, World!"}

    assert parse_headers_mock.called is False


def test_request_handler_with_missing_request_id(mocker: MockerFixture):
    parse_headers_mock = mocker.patch("nrlf.core.decorators.parse_headers")

    @request_handler(skip_request_verification=False)
    def decorated_function(event, context) -> Response:
        return Response(
            statusCode="200",
            body=json.dumps({"message": "Hello, World!"}),
            headers={"Content-Type": "application/json"},
        )

    event = create_test_api_gateway_event()
    context = create_mock_context()

    event["headers"].pop(X_REQUEST_ID_HEADER)

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
                            "code": "MISSING_OR_INVALID_HEADER",
                            "display": "There is a required header missing or invalid",
                        }
                    ]
                },
                "diagnostics": "The X-Request-Id header is missing or invalid",
            }
        ],
    }

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
            **create_headers(),
            "nhsd-connection-metadata": "invalid",
            "nhsd-client-rp-details": "invalid",
        }
    )
    context = create_mock_context()

    result = decorated_function(event, context)

    assert result["statusCode"] == "401"
    assert result["headers"] == default_response_headers()
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


def test_request_load_connection_metadata_with_permission_headers():
    expected_metadata = load_connection_metadata(
        headers=create_headers(nrl_permissions=[PERMISSION_ALLOW_ALL_POINTER_TYPES]),
        config=Config(),
    )

    assert expected_metadata.pointer_types == PointerTypes.list()


def test_request_load_connection_metadata_with_no_permission_lookup_or_file():
    expected_metadata = load_connection_metadata(
        headers=create_headers(nrl_app_id="someId"), config=Config()
    )

    assert expected_metadata.pointer_types == []


def test_request_parse_permission_file_with_no_permission_file():
    expected_metadata = parse_permissions_file(
        connection_metadata=parse_headers(create_headers(ods_code="SomeCode")),
    )

    assert expected_metadata == []


def test_request_parse_permission_file_with_permission_file():
    expected_metadata = parse_permissions_file(
        connection_metadata=parse_headers(create_headers(ods_code="TestCode")),
    )

    assert expected_metadata == ["http://snomed.info/sct|736253001"]


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
    assert result["headers"] == {
        "Content-Type": "application/json",
        **default_response_headers(),
    }
    assert result["isBase64Encoded"] is False

    parsed_body = json.loads(result["body"])
    assert parsed_body == {"message": "Hello, World!"}

    repository_mock.assert_called_once()
    assert repository_mock.call_args.kwargs == {
        "table_name": "unit-test-document-pointer",
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
