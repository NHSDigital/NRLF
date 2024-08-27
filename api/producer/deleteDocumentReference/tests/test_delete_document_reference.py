import json

from moto import mock_aws

from api.producer.deleteDocumentReference.delete_document_reference import handler
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.tests.data import load_document_reference
from nrlf.tests.dynamodb import mock_repository
from nrlf.tests.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
    default_response_headers,
)


@mock_aws
@mock_repository
def test_delete_document_reference_happy_path(repository: DocumentPointerRepository):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(), path_parameters={"id": "Y05868-99999-99999-999999"}
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "200",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "coding": [
                        {
                            "code": "RESOURCE_DELETED",
                            "display": "Resource deleted",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ]
                },
                "diagnostics": "The requested DocumentReference has been deleted",
            }
        ],
    }

    assert repository.get_by_id("Y05868-99999-99999-999999") is None


def test_delete_document_reference_invalid_id_in_path():
    event = create_test_api_gateway_event(headers=create_headers(), path_parameters={})

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

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
                            "code": "INVALID_PARAMETER",
                            "display": "Invalid parameter",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "Invalid path parameter (id: field required)",
                "expression": ["id"],
            }
        ],
    }


def test_delete_document_reference_invalid_producer_id():
    event = create_test_api_gateway_event(
        headers=create_headers(), path_parameters={"id": "X26-99999-99999-999999"}
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "403",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "forbidden",
                "details": {
                    "coding": [
                        {
                            "code": "AUTHOR_CREDENTIALS_ERROR",
                            "display": "Author credentials error",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The requested DocumentReference cannot be deleted because it belongs to another organisation",
            }
        ],
    }


@mock_aws
@mock_repository
def test_delete_document_reference_not_exists(repository: DocumentPointerRepository):
    event = create_test_api_gateway_event(
        headers=create_headers(), path_parameters={"id": "Y05868-99999-99999-999999"}
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "404",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "not-found",
                "details": {
                    "coding": [
                        {
                            "code": "NO_RECORD_FOUND",
                            "display": "No record found",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The requested DocumentReference could not be found",
            }
        ],
    }
