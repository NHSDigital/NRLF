import json

from nrlf.core.response import Response
from nrlf.producer.fhir.r4 import model as producer_model


def test_from_resource():
    resource = producer_model.DocumentReference.construct(id="test-doc-ref")
    response = Response.from_resource(
        resource,
        statusCode="201",
        headers={"Content-Type": "application/json"},
        isBase64Encoded=True,
    )
    assert isinstance(response, Response)
    assert response.statusCode == "201"
    assert response.headers == {"Content-Type": "application/json"}
    assert response.isBase64Encoded is True

    parsed_body = json.loads(response.body)
    assert parsed_body == {"id": "test-doc-ref"}


def test_from_issues():
    response = Response.from_issues(
        issues=[
            producer_model.OperationOutcomeIssue(
                severity="error",
                code="invalid",
                details=producer_model.CodeableConcept(text="Invalid input"),
            )
        ],
        statusCode="400",
        headers={"Content-Type": "application/json"},
        isBase64Encoded=False,
    )

    assert isinstance(response, Response)
    assert response.statusCode == "400"
    assert response.headers == {"Content-Type": "application/json"}
    assert response.isBase64Encoded is False

    body = json.loads(response.body)
    assert body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "invalid",
                "details": {"text": "Invalid input"},
            }
        ],
    }


def test_from_exception():
    exc = Exception("Something went wrong")

    response = Response.from_exception(exc)

    assert isinstance(response, Response)

    assert response.statusCode == "500"
    assert response.headers == {}
    assert response.isBase64Encoded is False

    body = json.loads(response.body)
    assert body == {
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
