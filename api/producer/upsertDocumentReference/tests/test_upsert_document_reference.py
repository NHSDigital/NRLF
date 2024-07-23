import json

from freezegun import freeze_time
from moto import mock_aws
from pytest import mark

from api.producer.upsertDocumentReference.upsert_document_reference import (
    _set_upsert_time_fields,
    handler,
)
from nrlf.core.constants import PERMISSION_SUPERSEDE_IGNORE_DELETE_FAIL
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.producer.fhir.r4.model import (
    DocumentReferenceRelatesTo,
    Identifier,
    Reference,
)
from nrlf.tests.data import load_document_reference, load_document_reference_data
from nrlf.tests.dynamodb import mock_repository
from nrlf.tests.events import (
    create_headers,
    create_mock_context,
    create_test_api_gateway_event,
)


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
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
        "headers": {
            "Location": "/producer/FHIR/R4/DocumentReference/Y05868-99999-99999-999999"
        },
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
    assert created_doc_pointer.created_on == "2024-03-21T12:34:56.789Z"
    assert created_doc_pointer.updated_on is None
    assert json.loads(created_doc_pointer.document) == {
        **json.loads(doc_ref_data),
        "meta": {
            "lastUpdated": "2024-03-21T12:34:56.789Z",
        },
        "date": "2024-03-21T12:34:56.789Z",
    }


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
def test_create_document_reference_happy_path_with_ssp(
    repository: DocumentPointerRepository,
):
    doc_ref_data = load_document_reference_data(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref_data,
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/producer/FHIR/R4/DocumentReference/Y05868-99999-99999-999999"
        },
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
    assert created_doc_pointer.created_on == "2024-03-21T12:34:56.789Z"
    assert created_doc_pointer.updated_on is None
    assert json.loads(created_doc_pointer.document) == {
        **json.loads(doc_ref_data),
        "meta": {
            "lastUpdated": "2024-03-21T12:34:56.789Z",
        },
        "date": "2024-03-21T12:34:56.789Z",
    }


def test_create_document_reference_invalid_category_type():
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    assert doc_ref.category and doc_ref.category[0].coding
    doc_ref.category[0].coding[0].code = "1102421000000108"
    doc_ref.category[0].coding[0].display = "Observations"

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
                "diagnostics": "The Category code of the provided document 'http://snomed.info/sct|1102421000000108' must match the allowed category for pointer type 'http://snomed.info/sct|736253002' with a category value of 'http://snomed.info/sct|734163000'",
                "expression": ["category.coding[0].code"],
            }
        ],
    }


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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ],
                },
                "diagnostics": "Request body is required",
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
                "diagnostics": "The id of the provided DocumentReference does not include the expected ODS code for this organisation",
            }
        ],
    }


def test_create_document_reference_with_no_custodian():
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
                "diagnostics": "The custodian of the provided DocumentReference does not match the expected ODS code for this organisation",
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
        "statusCode": "403",
        "headers": {},
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
                "diagnostics": "The type of the provided DocumentReference is not in the list of allowed types for this organisation",
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
                "diagnostics": "The relatesTo target identifier value does not include the expected ODS code for this organisation",
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
                identifier=Identifier(value="Y05868-99999-99999-999999"),
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
def test_create_document_reference_invalid_relatesto_not_exists_still_creates_with_ignore_perm(
    repository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="transforms",
            target=Reference(
                reference=None,
                identifier=Identifier(value="Y05868-99999-99999-999999"),
            ),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(
            nrl_permissions=[PERMISSION_SUPERSEDE_IGNORE_DELETE_FAIL]
        ),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/producer/FHIR/R4/DocumentReference/Y05868-99999-99999-999999"
        },
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
            app_id="12356",
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
def test_create_document_reference_with_no_context_related_for_ssp_url(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-ssp-content")

    del doc_ref.context.related

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
                    ]
                },
                "diagnostics": "Missing context.related. It must be provided and contain a single valid ASID identifier when content contains an SSP URL",
                "expression": ["context.related"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_with_no_asid_in_for_ssp_url(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-ssp-content")

    doc_ref.context.related = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/not-an-asid",
                "value": "some-other-value",
            }
        }
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
                "diagnostics": "Missing ASID identifier. context.related must contain a single valid ASID identifier when content contains an SSP URL",
                "expression": ["context.related"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_create_document_reference_with_invalid_asid_for_ssp_url(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-ssp-content")

    doc_ref.context.related = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                "value": "not-a-valid-asid",
            }
        }
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
                "code": "value",
                "details": {
                    "coding": [
                        {
                            "code": "INVALID_IDENTIFIER_VALUE",
                            "display": "Invalid identifier value",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "Invalid ASID value 'not-a-valid-asid'. A single ASID consisting of 12 digits can be provided in the context.related field.",
                "expression": ["context.related[0].identifier.value"],
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
    doc_ref.id = "Y05868-99999-99999-111111"
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="replaces",
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
        "statusCode": "201",
        "headers": {
            "Location": "/producer/FHIR/R4/DocumentReference/Y05868-99999-99999-111111"
        },
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
def test_create_document_reference_supersede_succeeds_with_toggle(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    # Add reference to a non-existing pointer
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="replaces",
            target=Reference(
                reference=None, identifier=Identifier(value="Y05868-99999-99999-000000")
            ),
        )
    ]

    event = create_test_api_gateway_event(
        headers=create_headers(nrl_permissions=["supersede-ignore-delete-fail"]),
        body=doc_ref.json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/producer/FHIR/R4/DocumentReference/Y05868-99999-99999-999999"
        },
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

    non_existent_pointer = repository.get_by_id("Y05868-99999-99999-000000")
    assert non_existent_pointer is None


@mock_aws
@mock_repository
def test_create_document_reference_supersede_fails_without_toggle(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    # Add reference to a non-existing pointer
    doc_ref.relatesTo = [
        DocumentReferenceRelatesTo(
            code="replaces",
            target=Reference(
                reference=None, identifier=Identifier(value="Y05868-99999-99999-000000")
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
def test_create_document_reference_create_relatesto_not_replaces(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    # Change document ID and NHS number
    doc_ref.id = "Y05868-99999-99999-111111"
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
        "statusCode": "201",
        "headers": {
            "Location": "/producer/FHIR/R4/DocumentReference/Y05868-99999-99999-111111"
        },
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


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
def test_create_document_reference_with_date_ignored(
    repository: DocumentPointerRepository,
):
    doc_ref_data = load_document_reference_data("Y05868-736253002-Valid-with-date")

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref_data,
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/producer/FHIR/R4/DocumentReference/Y05868-99999-99999-999999"
        },
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
    assert created_doc_pointer.created_on == "2024-03-21T12:34:56.789Z"
    assert created_doc_pointer.updated_on is None
    assert json.loads(created_doc_pointer.document) == {
        **json.loads(doc_ref_data),
        "meta": {
            "lastUpdated": "2024-03-21T12:34:56.789Z",
        },
        "date": "2024-03-21T12:34:56.789Z",
    }


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
def test_create_document_reference_with_date_and_meta_lastupdated_ignored(
    repository: DocumentPointerRepository,
):
    doc_ref_data = load_document_reference_data(
        "Y05868-736253002-Valid-with-date-and-meta-lastupdated"
    )

    event = create_test_api_gateway_event(
        headers=create_headers(),
        body=doc_ref_data,
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/producer/FHIR/R4/DocumentReference/Y05868-99999-99999-999999"
        },
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
    assert created_doc_pointer.created_on == "2024-03-21T12:34:56.789Z"
    assert created_doc_pointer.updated_on is None
    assert json.loads(created_doc_pointer.document) == {
        **json.loads(doc_ref_data),
        "meta": {
            "lastUpdated": "2024-03-21T12:34:56.789Z",
        },
        "date": "2024-03-21T12:34:56.789Z",
    }


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
def test_create_document_reference_with_date_overidden(
    repository: DocumentPointerRepository,
):
    doc_ref_data = load_document_reference_data("Y05868-736253002-Valid-with-date")

    event = create_test_api_gateway_event(
        headers=create_headers(nrl_permissions=["audit-dates-from-payload"]),
        body=doc_ref_data,
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "201",
        "headers": {
            "Location": "/producer/FHIR/R4/DocumentReference/Y05868-99999-99999-999999"
        },
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
    assert created_doc_pointer.created_on == "2024-03-21T12:34:56.789Z"
    assert created_doc_pointer.updated_on is None
    assert json.loads(created_doc_pointer.document) == {
        **json.loads(doc_ref_data),
        "meta": {
            "lastUpdated": "2024-03-21T12:34:56.789Z",
        },
        "date": "2024-03-20T00:00:01.000Z",
    }


@freeze_time("2024-03-25")
@mark.parametrize(
    "doc_ref_name",
    [
        "Y05868-736253002-Valid",
        "Y05868-736253002-Valid-with-date",
        "Y05868-736253002-Valid-with-date-and-meta-lastupdated",
    ],
)
def test__set_create_time_fields(doc_ref_name: str):
    test_time = "2024-03-24T12:34:56.789Z"
    test_doc_ref = load_document_reference(doc_ref_name)
    test_perms = []

    response = _set_upsert_time_fields(test_time, test_doc_ref, test_perms)

    assert response.dict(exclude_none=True) == {
        **test_doc_ref.dict(exclude_none=True),
        "meta": {
            "lastUpdated": "2024-03-24T12:34:56.789Z",
        },
        "date": "2024-03-24T12:34:56.789Z",
    }


@freeze_time("2024-03-25")
@mark.parametrize(
    "doc_ref_name",
    [
        "Y05868-736253002-Valid-with-date",
        "Y05868-736253002-Valid-with-date-and-meta-lastupdated",
    ],
)
def test__set_create_time_fields_when_doc_has_date_and_perms(doc_ref_name: str):
    test_time = "2024-03-24T12:34:56.789Z"
    test_doc_ref = load_document_reference(doc_ref_name)
    test_perms = ["audit-dates-from-payload"]

    response = _set_upsert_time_fields(test_time, test_doc_ref, test_perms)

    assert response.dict(exclude_none=True) == {
        **test_doc_ref.dict(exclude_none=True),
        "meta": {
            "lastUpdated": test_time,
        },
        "date": test_doc_ref.date,
    }


@freeze_time("2024-03-25")
def test__set_create_time_fields_when_no_date_but_perms():
    test_time = "2024-03-24T12:34:56.789Z"
    test_doc_ref = load_document_reference("Y05868-736253002-Valid")
    test_perms = ["audit-dates-from-payload"]

    response = _set_upsert_time_fields(test_time, test_doc_ref, test_perms)

    assert response.dict(exclude_none=True) == {
        **test_doc_ref.dict(exclude_none=True),
        "meta": {
            "lastUpdated": test_time,
        },
        "date": test_time,
    }
