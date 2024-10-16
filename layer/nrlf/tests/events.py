import json
from typing import Dict, List, Optional
from unittest.mock import Mock


def create_default_request_headers(headers: dict = {}) -> dict:
    return {
        **headers,
    }


def create_headers(
    ods_code: str = "Y05868",
    nrl_permissions: Optional[List[str]] = [],
    app_name: Optional[str] = "TestApp",
    app_id: Optional[str] = "12345",
    nrl_app_id: Optional[str] = "Y05868-TestApp-12345678",
    additional_headers: Optional[Dict[str, str]] = {},
) -> Dict[str, str]:
    return {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.ods-code": ods_code,
                "nrl.permissions": nrl_permissions,
                "nrl.app-id": nrl_app_id,
                "nrl.test-event": True,
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {"developer.app.name": app_name, "developer.app.id": app_id}
        ),
        "X-Request-Id": "test_request_id",
        "NHSD-Correlation-Id": "test_correlation_id",
        **additional_headers,
    }


def default_response_headers():
    return {
        "X-Request-Id": "test_request_id",
    }


def create_test_api_gateway_event(
    headers: Optional[Dict[str, str]] = {},
    query_string_parameters: Optional[Dict[str, str]] = None,
    path_parameters: Optional[Dict[str, str]] = None,
    body: Optional[str] = None,
):
    return {
        "resource": "/",
        "path": "/",
        "httpMethod": "GET",
        "requestContext": {
            "resourcePath": "/",
            "httpMethod": "GET",
            "path": "/Prod/",
        },
        "headers": headers or create_headers(),
        "multiValueHeaders": {},
        "queryStringParameters": query_string_parameters or {},
        "multiValueQueryStringParameters": None,
        "pathParameters": path_parameters,
        "stageVariables": None,
        "body": body,
        "isBase64Encoded": None,
    }


def create_mock_context():
    return Mock(
        function_name="test_function",
        function_version="1",
        invoked_function_arn="arn:aws:lambda:eu-west-2:123456789012:function:test_function:1",
    )
