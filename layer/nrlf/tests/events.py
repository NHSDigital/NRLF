import json
from typing import Dict, List, Optional
from unittest.mock import Mock

from nrlf.core.constants import PointerTypes


def create_headers(
    ods_code: str = "Y05868",
    pointer_types: Optional[List[str]] = [PointerTypes.MENTAL_HEALTH_PLAN.value],
    nrl_permissions: Optional[List[str]] = [],
    app_name: Optional[str] = "TestApp",
    app_id: Optional[str] = "12345",
) -> Dict[str, str]:
    return {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": pointer_types,
                "nrl.ods-code": ods_code,
                "nrl.permissions": nrl_permissions,
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {"developer.app.name": app_name, "developer.app.id": app_id}
        ),
    }


def create_test_api_gateway_event(
    headers: Optional[Dict[str, str]] = None,
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
        "headers": headers or {},
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
