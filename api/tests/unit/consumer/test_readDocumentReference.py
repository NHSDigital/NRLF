import json

from moto import mock_aws

from api.consumer.readDocumentReference.index import handler
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
def test_read_document_reference_happy_path(repository: DocumentPointerRepository):
    # Create the document pointer
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
    assert parsed_body == doc_ref.dict(exclude_none=True)


@mock_aws
@mock_repository
def test_read_document_reference_not_found(repository: DocumentPointerRepository):
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
                "diagnostics": "The requested DocumentReference could not be found",
            }
        ],
    }


def test_read_document_reference_missing_id():
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
