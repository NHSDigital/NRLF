import json

from moto import mock_aws

from api.producer.deleteDocumentReference.index import handler
from api.tests.utilities.data import load_document_reference
from api.tests.utilities.dynamodb import mock_repository
from api.tests.utilities.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
)
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository


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

    assert result == {"statusCode": "200", "headers": {}, "isBase64Encoded": False}

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
                "diagnostics": "The requested document pointer has been deleted",
            }
        ],
    }

    assert repository.get_by_id("Y05868-99999-99999-999999") is None


def test_delete_document_reference_invalid_id_in_path():
    event = create_test_api_gateway_event(headers=create_headers(), path_parameters={})

    result = handler(event, create_mock_context())
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
                            "code": "INVALID_IDENTIFIER_VALUE",
                            "display": "Invalid identifier value",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "Invalid document reference ID provided in the path parameters",
            }
        ],
    }


def test_delete_document_reference_invalid_producer_id():
    event = create_test_api_gateway_event(
        headers=create_headers(), path_parameters={"id": "X26-99999-99999-999999"}
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {"statusCode": "401", "headers": {}, "isBase64Encoded": False}

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
                "diagnostics": "The requested document pointer cannot be deleted because it belongs to another organisation",
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

    assert result == {"statusCode": "404", "headers": {}, "isBase64Encoded": False}

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
                "diagnostics": "The requested document pointer could not be found",
            }
        ],
    }
