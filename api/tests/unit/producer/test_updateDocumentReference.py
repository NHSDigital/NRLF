import json

from moto import mock_aws

from api.producer.updateDocumentReference.index import handler
from api.tests.utilities.data import load_document_reference
from api.tests.utilities.dynamodb import mock_repository
from api.tests.utilities.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
)
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.producer.fhir.r4.model import DocumentReference


@mock_aws
@mock_repository
def test_update_document_reference_happy_path(repository: DocumentPointerRepository):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    existing_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")
    assert existing_doc_pointer is not None

    existing_doc_ref = DocumentReference.parse_raw(existing_doc_pointer.document)
    assert existing_doc_ref.docStatus == "final"

    doc_ref.docStatus = "entered-in-error"
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.json(),
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
                            "code": "RESOURCE_UPDATED",
                            "display": "Resource updated",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ]
                },
                "diagnostics": "The DocumentReference has been updated",
            }
        ],
    }

    updated_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")
    assert updated_doc_pointer is not None

    updated_doc_ref = DocumentReference.parse_raw(updated_doc_pointer.document)
    assert updated_doc_ref.docStatus == "entered-in-error"


def test_create_document_reference_no_body():
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=None,
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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "Request body is required",
            }
        ],
    }


def test_create_document_reference_invalid_body():
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body="{}",
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
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "Request body could not be parsed (resourceType: field required)",
                "expression": ["resourceType"],
            },
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
                "diagnostics": "Request body could not be parsed (status: field required)",
                "expression": ["status"],
            },
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
                "diagnostics": "Request body could not be parsed (content: field required)",
                "expression": ["content"],
            },
        ],
    }


def test_update_document_reference_no_id_in_path():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={},
        body=doc_ref.json(exclude_none=True),
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


def test_update_document_reference_id_mismatch():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "IDoNotMatch"},
        body=doc_ref.json(exclude_none=True),
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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The document id in the path does not match the document id in the body",
            }
        ],
    }


def test_update_document_reference_invalid_resource():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.custodian = None

    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.json(exclude_none=True),
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
                "code": "required",
                "details": {
                    "coding": [
                        {
                            "code": "INVALID_RESOURCE",
                            "display": "Invalid validation of resource",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The required field 'custodian' is missing",
                "expression": ["custodian"],
            }
        ],
    }


def test_update_document_reference_invalid_producer_id():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    event = create_test_api_gateway_event(
        headers=create_headers(ods_code="X26"),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())

    body = result.pop("body")

    assert result == {"statusCode": "403", "headers": {}, "isBase64Encoded": False}
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
                "diagnostics": "The id of the provided DocumentReference does not include the expected ODS code for this organisation",
            }
        ],
    }


@mock_aws
@mock_repository
def test_update_document_reference_no_existing_pointer(repository):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.json(exclude_none=True),
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


@mock_aws
@mock_repository
def test_update_document_reference_immutable_fields(repository):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    doc_ref.status = "draft"
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.json(exclude_none=True),
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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The field 'status' is immutable and cannot be updated",
                "expression": ["status"],
            }
        ],
    }
