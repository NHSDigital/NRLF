from unittest import mock

import pytest
from nrlf.core.constants import ID_SEPARATOR
from nrlf.core.errors import (
    DocumentReferenceValidationError,
    InvalidTupleError,
    ItemNotFound,
    RequestValidationError,
)
from nrlf.core.transform import make_timestamp
from nrlf.core.validators import (
    requesting_application_is_not_authorised,
    validate_document_reference_string,
    validate_nhs_number,
    validate_source,
    validate_timestamp,
    validate_tuple,
    validate_type_system,
)
from nrlf.producer.fhir.r4.model import RequestParams


@pytest.mark.parametrize(
    ["tuple", "expected_outcome"],
    (
        ["foo-bar", True],
        ["foo-bar-baz", True],
        ["foo", False],
    ),
)
def test_validate_tuple(tuple, expected_outcome):
    outcome = True
    try:
        validate_tuple(tuple=tuple, separator=ID_SEPARATOR)
    except InvalidTupleError:
        outcome = False
    assert expected_outcome == outcome


@pytest.mark.parametrize(
    ["nhs_number", "expected_outcome"],
    (
        ["2965487948", True],
        ["foo", False],
        ["123456", False],
    ),
)
def test_validate_nhs_number(nhs_number, expected_outcome):
    outcome = True
    try:
        validate_nhs_number(nhs_number=nhs_number)
    except ValueError:
        outcome = False
    assert expected_outcome == outcome


@mock.patch("nrlf.core.validators.VALID_SOURCES", {"foo", "bar"})
@pytest.mark.parametrize(
    ["source", "expected_outcome"],
    (["foo", True], ["bar", True], ["baz", False]),
)
def test_validate_source(source, expected_outcome):
    outcome = True
    try:
        validate_source(source=source)
    except ValueError:
        outcome = False
    assert expected_outcome == outcome


@pytest.mark.parametrize(
    ["date", "expected_outcome"],
    (
        ["2022-10-18T14:47:22.920Z", True],
        ["foo", False],
    ),
)
def test_validate_timestamp(date, expected_outcome):
    outcome = True
    try:
        validate_timestamp(date=date)
    except ValueError:
        outcome = False
    assert expected_outcome == outcome


def test_make_timestamp():
    timestamp = make_timestamp()
    validate_timestamp(timestamp)


@pytest.mark.parametrize(
    ["requesting_application_id", "authenticated_application_id", "expected_outcome"],
    (
        ["SCRa", "SCRa", False],
        ["SCRa", "APIM", True],
        ["APIM", "SCRA", True],
        ["SCRA", 4, True],
    ),
)
def test_requesting_application_is_not_authorised(
    requesting_application_id, authenticated_application_id, expected_outcome
):
    result = requesting_application_is_not_authorised(
        requesting_application_id, authenticated_application_id
    )

    assert result == expected_outcome


@pytest.mark.parametrize(
    ["document_reference_string", "expected_outcome"],
    (
        ["", DocumentReferenceValidationError],
        ["{}", DocumentReferenceValidationError],
        [
            """
            {
                "resourceType": "DocumentReference",
                "id": "8FW23-1114567891",
                "custodian": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/accredited-system-id",
                    "value": "8FW23"
                }
                },
                "subject": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": "9278693472"
                }
                },
                "type": {
                "coding": [
                    {
                    "system": "http://snomed.info/sct",
                    "code": "736253002"
                    }
                ]
                },
                "content": [
                {
                    "attachment": {
                    "contentType": "application/pdf",
                    "url": "https://example.org/my-doc.pdf"
                    }
                }
                ],
                "status": "current",
                "author": {

                }
            }
            """,
            DocumentReferenceValidationError,
        ],
        [
            """
            {
                "resourceType": "DocumentReference",
                "id": "8FW23-1114567891",
                "custodian": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/accredited-system-id",
                    "value": "8FW23"
                }
                },
                "subject": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": "9278693472"
                }
                },
                "type": {
                "coding": [
                    {
                    "system": "http://snomed.info/sct",
                    "code": "736253002"
                    }
                ]
                },
                "content": [
                {
                    "attachment": {
                    "contentType": "application/pdf",
                    "url": "https://example.org/my-doc.pdf"
                    }
                }
                ],
                "status": "current",
                "author":[
                    {
                        "identifier": {
                            "value": "Practitioner/A985657ZA"
                            }
                    }
                ]
            }
            """,
            None,
        ],
    ),
)
def test_is_document_reference_string_valid(
    document_reference_string, expected_outcome
):
    if type(expected_outcome) == type and issubclass(expected_outcome, Exception):
        with pytest.raises(expected_outcome):
            validate_document_reference_string(document_reference_string)
    else:
        assert validate_document_reference_string(document_reference_string) is None


@pytest.mark.parametrize(
    ["type_identifier", "pointer_types", "expected_outcome"],
    (
        [
            "https://nrl.team/rowan-test|123",
            ["https://nrl.team/rowan-poo|123"],
            RequestValidationError,
        ],
        [
            "https://nrl.team/rowan-test|123",
            ["https://nrl.team/rowan-poo|123", "https://nrl.team/rowan-test|123"],
            None,
        ],
        [
            "http://snomed.info/sct|861421000000109",
            [
                "https://nrl.team/rowan-poo|123",
                "http://snomed.info/sct|861421000000109",
            ],
            None,
        ],
        ["https://nrl.team/rowan-test|123", [], RequestValidationError],
    ),
)
def test_validate_type_system(type_identifier, pointer_types, expected_outcome):

    queryStringParameters = {
        "type.identifier": type_identifier,
    }
    request_params = RequestParams(**queryStringParameters or {})

    if expected_outcome is RequestValidationError:
        with pytest.raises(expected_outcome):
            validate_type_system(
                type_identifier=request_params.type_identifier,
                pointer_types=pointer_types,
            )
    else:
        assert (
            validate_type_system(
                type_identifier=request_params.type_identifier,
                pointer_types=pointer_types,
            )
            is None
        )
