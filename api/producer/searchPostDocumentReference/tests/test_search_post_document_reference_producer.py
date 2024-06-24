import json

from moto import mock_aws

from api.producer.searchPostDocumentReference.search_post_document_reference import (
    handler,
)
from nrlf.core.constants import PointerTypes
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
def test_search_document_reference_happy_path(repository: DocumentPointerRepository):
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
def test_search_document_reference_missing_nhs_number(
    repository: DocumentPointerRepository,
):
    event = create_test_api_gateway_event(headers=create_headers())

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


@mock_aws
@mock_repository
def test_search_document_reference_invalid_nhs_number(
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
                "expression": ["subject:identifier"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_search_document_reference_invalid_type(repository: DocumentPointerRepository):
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
                "code": "code-invalid",
                "details": {
                    "coding": [
                        {
                            "code": "INVALID_CODE_SYSTEM",
                            "display": "Invalid code system",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The provided type system does not match the allowed types for this organisation",
                "expression": ["type"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_search_document_reference_only_returns_custodian_pointers(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(ods_code="X26"),
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
def test_search_document_reference_filters_by_type(
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
                "type": PointerTypes.MENTAL_HEALTH_PLAN.value,
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
def test_search_document_reference_filters_by_pointer_types(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(
            app_id="12356", pointer_types=[PointerTypes.EOL_COORDINATION_SUMMARY.value]
        ),
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
def test_search_post_document_reference_invalid_json(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    doc_pointer.document = "invalid json"

    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=json.dumps(
            {"subject:identifier": "https://fhir.nhs.uk/Id/nhs-number|6700028191"}
        ),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {"statusCode": "500", "headers": {}, "isBase64Encoded": False}

    parsed_body = json.loads(body)
    assert parsed_body == {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "exception",
                "details": {
                    "coding": [
                        {
                            "code": "INTERNAL_SERVER_ERROR",
                            "display": "Unexpected internal server error",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "An error occurred whilst parsing the document reference search results",
            }
        ],
    }
