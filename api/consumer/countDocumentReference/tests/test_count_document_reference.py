import json

from moto import mock_aws

from api.consumer.countDocumentReference.count_document_reference import handler
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.tests.data import load_document_reference
from nrlf.tests.dynamodb import mock_repository
from nrlf.tests.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
)


@mock_aws
@mock_repository
def test_count_document_reference_happy_path(repository: DocumentPointerRepository):
    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
        },
    )

    result = handler(event, create_mock_context())  # type: ignore
    body = result.pop("body")

    assert result == {"statusCode": "200", "headers": {}, "isBase64Encoded": False}

    parsed_body = json.loads(body)
    assert parsed_body == {"resourceType": "Bundle", "type": "searchset", "total": 0}

    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    result = handler(event, create_mock_context())  # type: ignore
    body = result.pop("body")

    assert result == {"statusCode": "200", "headers": {}, "isBase64Encoded": False}

    parsed_body = json.loads(body)
    assert parsed_body == {"resourceType": "Bundle", "type": "searchset", "total": 1}


def test_count_document_reference_missing_nhs_number():
    event = create_test_api_gateway_event(headers=create_headers())

    result = handler(event, create_mock_context())  # type: ignore
    body = result.pop("body")

    assert result == {"statusCode": "400", "headers": {}, "isBase64Encoded": False}

    parsed_body = json.loads(body)
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
                "diagnostics": "Invalid query parameter (subject:identifier: field required)",
                "expression": ["subject:identifier"],
            }
        ],
    }


def test_count_document_reference_invalid_nhs_number():
    event = create_test_api_gateway_event(
        headers=create_headers(),
        query_string_parameters={
            "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|123"
        },
    )

    result = handler(event, create_mock_context())  # type: ignore
    body = result.pop("body")

    assert result == {"statusCode": "400", "headers": {}, "isBase64Encoded": False}

    parsed_body = json.loads(body)
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
                            "code": "INVALID_IDENTIFIER_VALUE",
                            "display": "Invalid identifier value",
                        }
                    ]
                },
                "diagnostics": "Invalid NHS number provided in the query parameters",
                "expression": ["subject:identifier"],
            }
        ],
    }
