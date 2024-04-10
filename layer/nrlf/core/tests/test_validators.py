from unittest.mock import Mock

import pytest

from nrlf.core.errors import ParseError
from nrlf.core.validators import (
    DocumentReferenceValidator,
    ValidationResult,
    validate_type_system,
)
from nrlf.producer.fhir.r4.model import (
    DocumentReference,
    OperationOutcomeIssue,
    RequestQueryType,
)
from nrlf.tests.data import load_document_reference_json


def test_validate_type_system_valid():
    type_ = RequestQueryType(__root__="http://snomed.info/sct|736253002")
    pointer_types = [
        "http://snomed.info/sct|736253002",
        "http://snomed.info/sct|736373009",
    ]
    assert validate_type_system(type_, pointer_types) is True


def test_validate_type_system_invalid():
    type_ = RequestQueryType(__root__="http://snomed.info/invalid|736373009")
    pointer_types = [
        "http://snomed.info/sct|736373009",
        "http://snomed.info/sct|736373009",
    ]
    assert validate_type_system(type_, pointer_types) is False


def test_validate_type_system_empty():
    type_ = None
    pointer_types = []
    assert validate_type_system(type_, pointer_types) is True


def test_validation_result_reset():
    validation_result = ValidationResult(
        resource=DocumentReference.construct(id="example_resource"),
        issues=[OperationOutcomeIssue.construct()],
    )

    assert validation_result.resource.id == "example_resource"

    validation_result.reset()
    assert validation_result.resource.id is None
    assert validation_result.issues == []


def test_validation_result_add_error():
    validation_result = ValidationResult(
        resource=DocumentReference.construct(), issues=[]
    )

    issue_code = "issue_code"
    error_code = "BAD_REQUEST"
    diagnostics = "diagnostics"
    field = "field"

    validation_result.add_error(issue_code, error_code, diagnostics, field)

    assert len(validation_result.issues) == 1
    assert validation_result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "issue_code",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "BAD_REQUEST",
                    "display": "Bad request",
                }
            ],
        },
        "diagnostics": "diagnostics",
        "expression": ["field"],
    }


def test_validation_result_add_error_no_error_code():
    validation_result = ValidationResult(
        resource=DocumentReference.construct(), issues=[]
    )

    issue_code = "issue_code"
    diagnostics = "diagnostics"
    field = "field"

    validation_result.add_error(
        issue_code=issue_code, diagnostics=diagnostics, field=field
    )

    assert len(validation_result.issues) == 1
    assert validation_result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "issue_code",
        "diagnostics": "diagnostics",
        "expression": ["field"],
    }


def test_validation_result_is_valid():
    validation_result = ValidationResult(
        resource=DocumentReference.construct(), issues=[]
    )

    assert validation_result.is_valid is True

    validation_result.issues = [
        OperationOutcomeIssue.construct(severity="information"),
    ]

    assert validation_result.is_valid is True

    validation_result.issues = [
        OperationOutcomeIssue.construct(severity="error"),
    ]
    assert validation_result.is_valid is False

    validation_result.issues = [
        OperationOutcomeIssue.construct(severity="fatal"),
    ]
    assert validation_result.is_valid is False


def test_document_reference_validator_init():
    validator = DocumentReferenceValidator()
    assert validator.result.resource.id is None
    assert validator.result.issues == []


def test_document_reference_validator_parse_valid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    result = validator.parse(document_ref_data)

    assert result.id == "Y05868-99999-99999-999999"
    assert result.status == "current"
    assert result.type
    assert result.type.coding
    assert result.type.coding[0].code == "736253002"


def test_document_reference_validator_parse_invalid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["id"] = {"value": "invalid"}
    document_ref_data["type"] = "invalid"

    with pytest.raises(ParseError) as error:
        validator.parse(document_ref_data)

    exc = error.value

    assert len(exc.issues) == 2
    assert exc.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_RESOURCE",
                    "display": "Invalid validation of resource",
                }
            ]
        },
        "diagnostics": "Failed to parse DocumentReference resource (id: str type expected)",
        "expression": ["id"],
    }
    assert exc.issues[1].dict(exclude_none=True) == {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_RESOURCE",
                    "display": "Invalid validation of resource",
                }
            ]
        },
        "diagnostics": "Failed to parse DocumentReference resource (type: value is not a valid dict)",
        "expression": ["type"],
    }


def test_validate_document_reference_valid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    result = validator.validate(document_ref_data)

    assert result.is_valid is True
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert result.issues == []


def test_validate_document_reference_missing_fields():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    del document_ref_data["id"]
    del document_ref_data["type"]
    del document_ref_data["custodian"]
    del document_ref_data["subject"]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id is None
    assert len(result.issues) == 4
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "required",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_RESOURCE",
                    "display": "Invalid validation of resource",
                }
            ]
        },
        "diagnostics": "The required field 'custodian' is missing",
        "expression": ["custodian"],
    }

    diagnostics = [issue.diagnostics for issue in result.issues]
    assert diagnostics == [
        "The required field 'custodian' is missing",
        "The required field 'id' is missing",
        "The required field 'type' is missing",
        "The required field 'subject' is missing",
    ]


def test_validate_document_reference_missing_fields_stops_validation():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    validator._validate_no_extra_fields = Mock()
    validator._validate_identifiers = Mock()
    validator._validate_relates_to = Mock()

    del document_ref_data["custodian"]
    result = validator.validate(document_ref_data)

    assert result.is_valid is False

    assert validator._validate_no_extra_fields.call_count == 0
    assert validator._validate_identifiers.call_count == 0
    assert validator._validate_relates_to.call_count == 0


def test_validate_document_reference_extra_fields():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["extra_field"] = "extra_value"

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_RESOURCE",
                    "display": "Invalid validation of resource",
                }
            ]
        },
        "diagnostics": "The resource contains extra fields",
    }


def test_validate_identifiers_no_custodian_identifier():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    del document_ref_data["custodian"]["identifier"]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "required",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_RESOURCE",
                    "display": "Invalid validation of resource",
                }
            ]
        },
        "diagnostics": "Custodian must have an identifier",
        "expression": ["custodian.identifier"],
    }


def test_validate_identifiers_no_subject_identifier():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    del document_ref_data["subject"]["identifier"]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 1
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "required",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_RESOURCE",
                    "display": "Invalid validation of resource",
                }
            ]
        },
        "diagnostics": "Subject must have an identifier",
        "expression": ["subject.identifier"],
    }


def test_validate_identifiers_invalid_systems():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["custodian"]["identifier"]["system"] = "invalid"
    document_ref_data["subject"]["identifier"]["system"] = "invalid"

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert result.resource.id == "Y05868-99999-99999-999999"
    assert len(result.issues) == 2
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_IDENTIFIER_SYSTEM",
                    "display": "Invalid identifier system",
                }
            ]
        },
        "diagnostics": "Provided custodian identifier system is not the ODS system (expected: 'https://fhir.nhs.uk/Id/ods-organization-code')",
        "expression": ["custodian.identifier.system"],
    }
    assert result.issues[1].dict(exclude_none=True) == {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_IDENTIFIER_SYSTEM",
                    "display": "Invalid identifier system",
                }
            ]
        },
        "diagnostics": "Provided subject identifier system is not the NHS number system (expected 'https://fhir.nhs.uk/Id/nhs-number')",
        "expression": ["subject.identifier.system"],
    }


def test_validate_relates_to_valid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["relatesTo"] = [
        {
            "code": "replaces",
            "target": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": "9999999999",
                }
            },
        }
    ]

    result = validator.validate(document_ref_data)

    assert result.is_valid is True


def test_validate_relates_to_invalid_code():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["relatesTo"] = [
        {
            "code": "invalid",
            "target": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": "9999999999",
                }
            },
        }
    ]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "value",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_CODE_VALUE",
                    "display": "Invalid code value",
                }
            ]
        },
        "diagnostics": "Invalid relatesTo code: invalid",
        "expression": ["relatesTo[0].code"],
    }


def test_validate_relates_to_no_target_identifier():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json("Y05868-736253002-Valid")

    document_ref_data["relatesTo"] = [{"code": "replaces", "target": {}}]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "required",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_IDENTIFIER_VALUE",
                    "display": "Invalid identifier value",
                }
            ]
        },
        "diagnostics": "relatesTo code 'replaces' must have a target identifier",
        "expression": ["relatesTo[0].target.identifier.value"],
    }


def test_validate_ssp_content_with_asid():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    result = validator.validate(document_ref_data)

    assert result.is_valid is True


def test_validate_ssp_content_without_any_context_related():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    del document_ref_data["context"]["related"]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "required",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_RESOURCE",
                    "display": "Invalid validation of resource",
                }
            ]
        },
        "diagnostics": "Missing context.related. It must be provided and contain a single valid ASID identifier when content contains an SSP URL",
        "expression": ["context.related"],
    }


def test_validate_ssp_content_without_asid_in_context_related():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    document_ref_data["context"]["related"] = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                "value": "Y05868",
            }
        }
    ]

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "required",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_RESOURCE",
                    "display": "Invalid validation of resource",
                }
            ]
        },
        "diagnostics": "Missing ASID identifier. context.related must contain a single valid ASID identifier when content contains an SSP URL",
        "expression": ["context.related"],
    }


def test_validate_ssp_content_with_invalid_asid_value():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    document_ref_data["context"]["related"][0]["identifier"][
        "value"
    ] = "TEST_INVALID_ASID"

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "value",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_IDENTIFIER_VALUE",
                    "display": "Invalid identifier value",
                }
            ]
        },
        "diagnostics": "Invalid ASID value 'TEST_INVALID_ASID'. context.related must contain a single valid ASID identifier when content contains an SSP URL",
        "expression": ["context.related[0].identifier.value"],
    }


def test_validate_ssp_content_with_invalid_asid_value_and_multiple_related():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    document_ref_data["context"]["related"] = [
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                "value": "Y05868",
            }
        }
    ]
    document_ref_data["context"]["related"].append(
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                "value": "Y09999",
            }
        }
    )
    document_ref_data["context"]["related"].append(
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                "value": "TEST_INVALID_ASID",
            }
        }
    )

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "value",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_IDENTIFIER_VALUE",
                    "display": "Invalid identifier value",
                }
            ]
        },
        "diagnostics": "Invalid ASID value 'TEST_INVALID_ASID'. context.related must contain a single valid ASID identifier when content contains an SSP URL",
        "expression": ["context.related[2].identifier.value"],
    }


def test_validate_ssp_content_with_multiple_asids():
    validator = DocumentReferenceValidator()
    document_ref_data = load_document_reference_json(
        "Y05868-736253002-Valid-with-ssp-content"
    )

    document_ref_data["context"]["related"][0]["identifier"][
        "value"
    ] = "TEST_INVALID_ASID"
    document_ref_data["context"]["related"].append(
        {
            "identifier": {
                "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                "value": "09876543210",
            }
        }
    )

    result = validator.validate(document_ref_data)

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].dict(exclude_none=True) == {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
                {
                    "system": "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    "code": "INVALID_RESOURCE",
                    "display": "Invalid validation of resource",
                }
            ]
        },
        "diagnostics": "Multiple ASID identifiers provided. context.related must contain a single valid ASID identifier when content contains an SSP URL",
        "expression": ["context.related"],
    }
