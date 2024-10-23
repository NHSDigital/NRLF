import json

from freezegun import freeze_time
from moto import mock_aws
from pytest import mark

from api.producer.updateDocumentReference.update_document_reference import (
    _set_update_time_fields,
    handler,
)
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.producer.fhir.r4.model import CodeableConcept, Coding, DocumentReference
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
@freeze_time("2024-03-21T12:34:56.789")
def test_update_document_reference_happy_path(repository: DocumentPointerRepository):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    existing_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")
    assert existing_doc_pointer is not None

    existing_doc_ref = DocumentReference.model_validate_json(
        existing_doc_pointer.document
    )
    assert existing_doc_ref.docStatus == "final"

    doc_ref.docStatus = "entered-in-error"
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.model_dump_json(),
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

    updated_doc_ref = DocumentReference.model_validate_json(
        updated_doc_pointer.document
    )
    assert updated_doc_ref.docStatus == "entered-in-error"

    assert updated_doc_ref.meta.lastUpdated == "2024-03-21T12:34:56.789Z"
    assert updated_doc_pointer.updated_on == "2024-03-21T12:34:56.789Z"
    assert updated_doc_pointer.created_on == existing_doc_pointer.created_on


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
def test_update_document_reference_happy_path_with_ssp(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-ssp-content")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    existing_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")
    assert existing_doc_pointer is not None

    existing_doc_ref = DocumentReference.model_validate_json(
        existing_doc_pointer.document
    )
    assert existing_doc_ref.docStatus == "final"

    doc_ref.docStatus = "entered-in-error"
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.model_dump_json(),
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

    updated_doc_ref = DocumentReference.model_validate_json(
        updated_doc_pointer.document
    )
    assert updated_doc_ref.docStatus == "entered-in-error"

    assert updated_doc_ref.meta.lastUpdated == "2024-03-21T12:34:56.789Z"
    assert updated_doc_pointer.updated_on == "2024-03-21T12:34:56.789Z"
    assert updated_doc_pointer.created_on == existing_doc_pointer.created_on


def test_create_document_reference_no_body():
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=None,
    )

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
                            "code": "MESSAGE_NOT_WELL_FORMED",
                            "display": "Message not well formed",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "Request body could not be parsed (resourceType: Field required)",
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
                "diagnostics": "Request body could not be parsed (status: Field required)",
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
                "diagnostics": "Request body could not be parsed (content: Field required)",
                "expression": ["content"],
            },
        ],
    }


def test_update_document_reference_no_id_in_path():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={},
        body=doc_ref.model_dump_json(exclude_none=True),
    )

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
                "diagnostics": "Invalid path parameter (id: Field required)",
                "expression": ["id"],
            }
        ],
    }


def test_update_document_reference_id_mismatch():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "IDoNotMatch"},
        body=doc_ref.model_dump_json(exclude_none=True),
    )

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
        body=doc_ref.model_dump_json(exclude_none=True),
    )

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
        headers=create_headers(ods_code="RQI"),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.model_dump_json(exclude_none=True),
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
        body=doc_ref.model_dump_json(exclude_none=True),
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


@mock_aws
@mock_repository
def test_update_document_reference_immutable_fields(repository):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    doc_ref.type = CodeableConcept(
        id=None,
        coding=[
            Coding(
                id=None,
                system="http://snomed.info/sct",
                version=None,
                code="1213324",
                display="Some Code",
                userSelected=None,
            )
        ],
        text=None,
        extension=None,
    )

    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.model_dump_json(exclude_none=True),
    )

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
                            "code": "BAD_REQUEST",
                            "display": "Bad request",
                            "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        }
                    ]
                },
                "diagnostics": "The field 'type' is immutable and cannot be updated",
                "expression": ["type"],
            }
        ],
    }


@mock_aws
@mock_repository
def test_update_document_reference_with_no_context_related_for_ssp_url(repository):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-ssp-content")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    del doc_ref.context.related

    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.model_dump_json(exclude_none=True),
    )

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
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.model_dump_json(exclude_none=True),
    )

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
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.model_dump_json(exclude_none=True),
    )

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
@freeze_time("2024-03-21T12:34:56.789")
def test_update_document_reference_with_meta_lastupdated_ignored(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-meta-lastupdated")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    existing_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")
    assert existing_doc_pointer is not None

    existing_doc_ref = DocumentReference.model_validate_json(
        existing_doc_pointer.document
    )
    assert existing_doc_ref.docStatus == "final"

    doc_ref.docStatus = "entered-in-error"
    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.model_dump_json(),
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

    updated_doc_ref = DocumentReference.model_validate_json(
        updated_doc_pointer.document
    )
    assert updated_doc_ref.docStatus == "entered-in-error"

    assert updated_doc_ref.meta.lastUpdated == "2024-03-21T12:34:56.789Z"
    assert updated_doc_pointer.updated_on == "2024-03-21T12:34:56.789Z"
    assert updated_doc_pointer.created_on == existing_doc_pointer.created_on


@mock_aws
@mock_repository
@freeze_time("2024-03-21T12:34:56.789")
def test_update_document_reference_with_invalid_date_ignored(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid-with-date")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    repository.create(doc_pointer)

    existing_doc_pointer = repository.get_by_id("Y05868-99999-99999-999999")
    assert existing_doc_pointer is not None

    existing_doc_ref = DocumentReference.model_validate_json(
        existing_doc_pointer.document
    )
    assert existing_doc_ref.docStatus == "final"

    doc_ref.date = "2024-05-04T11:11:10.111Z"
    doc_ref.docStatus = "entered-in-error"

    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.model_dump_json(),
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

    updated_doc_ref = DocumentReference.model_validate_json(
        updated_doc_pointer.document
    )
    assert updated_doc_ref.docStatus == "entered-in-error"
    assert updated_doc_ref.date == "2024-03-20T00:00:01.000Z"


@mock_aws
@mock_repository
def test_update_document_reference_existing_invalid_json(
    repository: DocumentPointerRepository,
):
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_pointer = DocumentPointer.from_document_reference(doc_ref)
    doc_pointer.document = "invalid json"
    repository.create(doc_pointer)

    event = create_test_api_gateway_event(
        headers=create_headers(),
        path_parameters={"id": "Y05868-99999-99999-999999"},
        body=doc_ref.model_dump_json(exclude_none=True),
    )

    result = handler(event, create_mock_context())
    body = result.pop("body")

    assert result == {
        "statusCode": "500",
        "headers": default_response_headers(),
        "isBase64Encoded": False,
    }

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
                "diagnostics": "An error occurred whilst parsing the existing document reference",
            }
        ],
    }


@freeze_time("2024-03-25")
@mark.parametrize(
    "doc_ref_name",
    [
        "Y05868-736253002-Valid-with-date",
        "Y05868-736253002-Valid-with-date-and-meta-lastupdated",
    ],
)
def test__set_update_time_fields(doc_ref_name: str):
    test_time = "2024-03-24T12:34:56.789Z"
    test_doc_ref = load_document_reference(doc_ref_name)

    response = _set_update_time_fields(test_time, test_doc_ref)

    assert response.model_dump(exclude_none=True) == {
        **test_doc_ref.model_dump(exclude_none=True),
        "meta": {
            "lastUpdated": test_time,
        },
        "date": test_doc_ref.date,
    }
