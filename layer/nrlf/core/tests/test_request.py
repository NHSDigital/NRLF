import json

import pytest

from nrlf.core.errors import OperationOutcomeError
from nrlf.core.request import parse_headers


def test_parse_headers_empty_headers():
    headers = {}

    with pytest.raises(OperationOutcomeError) as error:
        parse_headers(headers)

    exc = error.value

    assert exc.status_code == "401"
    assert exc.operation_outcome.dict(exclude_none=True) == {
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


def test_parse_headers_valid_headers():
    headers = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": ["pointer_type"],
                "nrl.ods-code": "X26",
                "nrl.ods-code-extension": "001",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.enable-authorization-lookup": True,
                "nrl.app-id": "X26-TestApp-12345",
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    metadata = parse_headers(headers)

    assert metadata.pointer_types == ["pointer_type"]
    assert metadata.ods_code == "X26"
    assert metadata.ods_code_extension == "001"
    assert metadata.nrl_app_id == "X26-TestApp-12345"
    assert metadata.nrl_permissions == ["permission1", "permission2"]
    assert metadata.enable_authorization_lookup is True
    assert metadata.client_rp_details.developer_app_name == "TestApp"
    assert metadata.client_rp_details.developer_app_id == "12345"
    assert metadata.ods_code_parts == ("X26", "001")


def test_parse_headers_invalid_headers():
    headers = {
        "nhsd-connection-metadata": "invalid",
        "nhsd-client-rp-details": "invalid",
    }

    with pytest.raises(OperationOutcomeError) as error:
        parse_headers(headers)

    exc = error.value

    assert exc.status_code == "401"
    assert exc.operation_outcome.dict(exclude_none=True) == {
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
                },
                "diagnostics": "Unable to parse metadata about the requesting application. Contact the onboarding team.",
            }
        ],
    }


def test_parse_headers_case_insensitive():
    headers = {
        "NHSD-Connection-Metadata": json.dumps(
            {
                "nrl.pointer-types": ["pointer_type"],
                "nrl.ods-code": "X26",
                "nrl.ods-code-extension": "001",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.enable-authorization-lookup": True,
                "nrl.app-id": "X26-App-12345",
            }
        ),
        "NHSD-Client-RP-Details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    metadata = parse_headers(headers)

    assert metadata.pointer_types == ["pointer_type"]
    assert metadata.ods_code == "X26"
    assert metadata.ods_code_extension == "001"
    assert metadata.nrl_app_id == "X26-App-12345"
    assert metadata.nrl_permissions == ["permission1", "permission2"]
    assert metadata.enable_authorization_lookup is True
    assert metadata.client_rp_details.developer_app_name == "TestApp"
    assert metadata.client_rp_details.developer_app_id == "12345"
    assert metadata.ods_code_parts == ("X26", "001")
