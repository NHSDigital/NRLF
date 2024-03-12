import json

from moto import mock_aws

from api.consumer.searchPostDocumentReference.index import handler
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
def test_search_post_document_reference_happy_path(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=json.dumps(
            {
                "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            }
        ),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {"statusCode": "200", "headers": {}, "isBase64Encoded": False}

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 1,
        "entry": [{"resource": doc_ref.dict(exclude_none=True)}],
    }


@mock_aws
@mock_repository
def test_search_document_reference_no_results(repository: DocumentPointerRepository):
    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=json.dumps(
            {
                "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
            }
        ),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {"statusCode": "200", "headers": {}, "isBase64Encoded": False}

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 0,
        "entry": [],
    }


@mock_aws
@mock_repository
def test_search_post_document_reference_missing_nhs_number(
    repository: DocumentPointerRepository,
):
    event = create_test_api_gateway_event(headers=create_headers(), body="{}")

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
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "Request body could not be parsed (subject:identifier: field required)",
                "expression": ["subject:identifier"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_search_post_document_reference_invalid_nhs_number(
    repository: DocumentPointerRepository,
):
    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=json.dumps(
            {"subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|123"}
        ),
    )

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
                            "code": "INVALID_NHS_NUMBER",
                            "display": "Invalid NHS number",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "A valid NHS number is required to search for document references",
            }
        ],
    }


@mock_aws
@mock_repository
def test_search_post_document_reference_invalid_type(
    repository: DocumentPointerRepository,
):
    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=json.dumps(
            {
                "subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191",
                "type": "https://fhir.nhs.uk/CodeSystem/Document-Type|invalid",
            }
        ),
    )

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
                            "code": "INVALID_CODE_VALUE",
                            "display": "Invalid code value",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The provided system type value does not match the allowed types",
            }
        ],
    }
