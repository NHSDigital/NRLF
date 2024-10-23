import json

import pytest
from pydantic import BaseModel, ValidationError

from nrlf.core.errors import OperationOutcomeError, ParseError
from nrlf.core.response import Response
from nrlf.producer.fhir.r4.model import CodeableConcept, OperationOutcomeIssue


def test_operation_outcome_error():
    severity = "error"
    code = "invalid"
    details = CodeableConcept(text="Invalid input")
    diagnostics = "Invalid input provided"
    expression = ["expression"]
    status_code = "400"

    error = OperationOutcomeError(
        severity, code, details, diagnostics, expression, status_code
    )

    assert isinstance(error, Exception)
    assert error.status_code == status_code

    assert error.operation_outcome.model_dump(exclude_none=True) == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": severity,
                "code": code,
                "details": {"text": "Invalid input"},
                "diagnostics": diagnostics,
                "expression": expression,
            }
        ],
    }

    response = error.response
    assert isinstance(response, Response)

    assert response.model_dump() == {
        "statusCode": status_code,
        "body": error.operation_outcome.model_dump_json(exclude_none=True, indent=2),
        "headers": {},
        "isBase64Encoded": False,
    }


def test_parse_error():
    issues = [
        OperationOutcomeIssue(
            severity="error",
            code="invalid",
            details=CodeableConcept(text="Invalid input"),
        )
    ]

    error = ParseError(issues)

    assert isinstance(error, Exception)
    assert error.issues == issues

    response = error.response
    assert isinstance(response, Response)

    assert error.response.model_dump() == {
        "statusCode": "400",
        "body": json.dumps(
            {
                "resourceType": "OperationOutcome",
                "issue": [
                    {
                        "severity": "error",
                        "code": "invalid",
                        "details": {"text": "Invalid input"},
                    }
                ],
            },
            indent=2,
        ),
        "headers": {},
        "isBase64Encoded": False,
    }


def test_parse_error_from_validation_error():
    class TestModel(BaseModel):
        test_field: str

    with pytest.raises(ValidationError) as error:
        TestModel.model_validate({})

    exc = error.value
    details = CodeableConcept(text="Invalid input")
    msg = "Validation failed"

    error = ParseError.from_validation_error(exc, details, msg)

    assert isinstance(error, Exception)
    assert [issue.model_dump(exclude_none=True) for issue in error.issues] == [
        {
            "severity": "error",
            "code": "invalid",
            "details": {"text": "Invalid input"},
            "diagnostics": "Validation failed (test_field: Field required)",
            "expression": ["test_field"],
        }
    ]

    response = error.response
    assert isinstance(response, Response)

    assert response.model_dump() == {
        "statusCode": "400",
        "body": json.dumps(
            {
                "resourceType": "OperationOutcome",
                "issue": [
                    {
                        "severity": "error",
                        "code": "invalid",
                        "details": {"text": "Invalid input"},
                        "diagnostics": "Validation failed (test_field: Field required)",
                        "expression": ["test_field"],
                    }
                ],
            },
            indent=2,
        ),
        "headers": {},
        "isBase64Encoded": False,
    }
