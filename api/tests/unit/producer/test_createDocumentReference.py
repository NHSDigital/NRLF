import json

from moto import mock_aws

from api.producer.createDocumentReference.index import handler
from api.tests.utilities.data import (
    load_document_reference,
    load_document_reference_data,
)
from api.tests.utilities.dynamodb import mock_repository
from api.tests.utilities.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
)
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.producer.fhir.r4.model import (
    DocumentReferenceRelatesTo,
    Identifier,
    Reference,
)


@mock_aws
@mock_repository
def test_create_document_reference_happy_path(repository: DocumentPointerRepository):
    doc_ref_data = load_document_reference_data("Y05868-736253002-Valid")

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref_data,
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {},
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
                            "code": "RESOURCE_CREATED",
                            "display": "Resource created",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ],
                },
                "diagnostics": "The document has been created",
            }
        ],
    }

    created_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")

    assert created_doc_pointer is not None
    assert json.loads(created_doc_pointer.document) == json.loads(doc_ref_data)


def test_create_document_reference_no_body():
    event = create_test_api_gateway_event(
        headers=create_headers(),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": {},
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
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ],
                },
                "diagnostics": "Request body could not be parsed (__root__: Expecting value: line 1 column 1 (char 0))",
                "expression": ["__root__"],
            }
        ],
    }


def test_create_document_reference_invalid_body():
    event = create_test_api_gateway_event(
        headers=create_headers(),
        body="{}",
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": {},
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
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ],
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
                    ],
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
                    ],
                },
                "diagnostics": "Request body could not be parsed (content: field required)",
                "expression": ["content"],
            },
        ],
    }


def test_create_document_reference_invalid_resource():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.custodian = None

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": {},
        "isBase64Encoded": False,
    }

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
                    ],
                },
                "diagnostics": "The required field 'custodian' is missing",
                "expression": ["custodian"],
            },
        ],
    }


def test_create_document_reference_invalid_producer_id():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.id = "X26-99999-99999-999999"

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": {},
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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The id of the provided document pointer does not include the expected organisation code for this app",
            }
        ],
    }


def test_create_document_reference_invalid_custodian_id():
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    assert doc_ref.custodian and doc_ref.custodian.identifier
    doc_ref.custodian.identifier.value = "X26"

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": {},
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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The custodian of the provided document pointer does not match the expected organisation code for this app",
                "expression": ["custodian.identifier.value"],
            }
        ],
    }


def test_create_document_reference_invalid_pointer_type():
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    assert doc_ref.type and doc_ref.type.coding
    doc_ref.type.coding[0].code = "invalid"

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "401",
        "headers": {},
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
                            "code": "AUTHOR_CREDENTIALS_ERROR",
                            "display": "Author credentials error",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The type of the provided document pointer is not in the list of allowed types for this app",
                "expression": ["type.coding[0].code"],
            }
        ],
    }


def test_create_document_reference_no_relatesto_target():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms", target=Reference(reference=None, identifier=None)
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": {},
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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "No identifier value provided for relatesTo target",
                "expression": ["relatesTo[0].target.identifier.value"],
            }
        ],
    }


def test_create_document_reference_invalid_relatesto_target_producer_id():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms",
            target=Reference(
                reference=None, identifier=Identifier(value="X26-99999-99999-999999")
            ),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": {},
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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The relatesTo target identifier value does not include the expected organisation code for this app",
                "expression": ["relatesTo[0].target.identifier.value"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_invalid_relatesto_not_exists(repository):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms",
            target=Reference(
                reference=None,
                identifier=Identifier(value="Y05868-123456-123456-123456"),
            ),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": {},
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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The relatesTo target document does not exist",
                "expression": ["relatesTo[0].target.identifier.value"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_invalid_relatesto_nhs_number(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Change document ID and NHS number
    doc_ref.id = "Y05868-99999-99999-123456"

    assert doc_ref.subject and doc_ref.subject.identifier
    doc_ref.subject.identifier.value = "9999999999"
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms",
            target=Reference(
                reference=None, identifier=Identifier(value="Y05868-99999-99999-999999")
            ),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": {},
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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The relatesTo target document NHS number does not match the NHS number in the request",
                "expression": ["relatesTo[0].target.identifier.value"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_invalid_relatesto_type(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Change document ID and NHS number
    doc_ref.id = "Y05868-99999-99999-123456"

    assert doc_ref.type and doc_ref.type.coding
    doc_ref.type.coding[0].code = "861421000000109"
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms",
            target=Reference(
                reference=None, identifier=Identifier(value="Y05868-99999-99999-999999")
            ),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(
            pointer_types=[
                "http://snomed.info/sct|861421000000109",
                "http://snomed.info/sct|736253002",
            ]
        ),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "400",
        "headers": {},
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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The relatesTo target document type does not match the type in the request",
                "expression": ["relatesTo[0].target.identifier.value"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_supersede_deletes_old_pointers_replace(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Change document ID and NHS number
    doc_ref.id = "Y05868-99999-99999-123456"
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="replaces",
            target=Reference(
                reference=None, identifier=Identifier(value="Y05868-99999-99999-999999")
            ),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(
            pointer_types=[
                "http://snomed.info/sct|861421000000109",
                "http://snomed.info/sct|736253002",
            ]
        ),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {},
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
                            "code": "RESOURCE_SUPERSEDED",
                            "display": "Resource created and resource(s) deleted",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ]
                },
                "diagnostics": "The document has been superseded by a new version",
            }
        ],
    }

    old_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")
    assert old_doc_pointer is None


@mock_aws
@mock_repository
def test_create_document_reference_create_relatesto_not_replaces(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Change document ID and NHS number
    doc_ref.id = "Y05868-99999-99999-123456"
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms",
            target=Reference(
                reference=None, identifier=Identifier(value="Y05868-99999-99999-999999")
            ),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(
            pointer_types=[
                "http://snomed.info/sct|861421000000109",
                "http://snomed.info/sct|736253002",
            ]
        ),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {},
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
                            "code": "RESOURCE_CREATED",
                            "display": "Resource created",
                            "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                        }
                    ]
                },
                "diagnostics": "The document has been created",
            }
        ],
    }

    old_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")
    assert old_doc_pointer is not None
