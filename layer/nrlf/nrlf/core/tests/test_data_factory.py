from .data_factory import (
    APIM_PATIENT_SUCCESS,
    CONTENT_EXAMPLE_PDF_MIME,
    CONTENT_EXAMPLE_PDF_URL,
    FHIR_SYSTEMS_ASID,
    FHIR_SYSTEMS_NHS_NUMBER,
    NRL_ODS_SUCCESS,
    SNOMED_CODES_MENTAL_HEALTH_CRISIS_PLAN,
    SNOMED_SYSTEM,
    _strip_none,
    generate_test_attachment,
    generate_test_content,
    generate_test_custodian,
    generate_test_document_reference,
    generate_test_document_type,
    generate_test_id,
    generate_test_relates_to,
    generate_test_subject,
)

"""
We're going to be relying that the outputs for these test
function quite heavily so we need to ensure they are tested
"""


def test_strip_none():
    actual = _strip_none({"foo": 1, "bar": None})
    expected = {"foo": 1}
    assert actual == expected


def test_id():
    actual = generate_test_id(provider_id="RJ11", local_document_id="999")
    expected = "RJ11|999"
    assert actual == expected


def test_attachment():
    actual = generate_test_attachment()
    expected = {
        "contentType": CONTENT_EXAMPLE_PDF_MIME,
        "url": CONTENT_EXAMPLE_PDF_URL,
    }
    assert actual == expected


def test_content():
    actual = generate_test_content()
    expected = [
        {
            "attachment": {
                "contentType": CONTENT_EXAMPLE_PDF_MIME,
                "url": CONTENT_EXAMPLE_PDF_URL,
            }
        }
    ]
    assert actual == expected


def test_document_type():
    actual = generate_test_document_type()
    expected = {
        "coding": [
            {
                "system": SNOMED_SYSTEM,
                "code": SNOMED_CODES_MENTAL_HEALTH_CRISIS_PLAN,
            }
        ]
    }
    assert actual == expected


def test_subject():
    actual = generate_test_subject()
    expected = {
        "identifier": {
            "system": FHIR_SYSTEMS_NHS_NUMBER,
            "value": APIM_PATIENT_SUCCESS,
        }
    }
    assert actual == expected


def test_custodian():
    actual = generate_test_custodian()
    expected = {
        "identifier": {
            "system": FHIR_SYSTEMS_ASID,
            "value": NRL_ODS_SUCCESS,
        }
    }
    assert actual == expected


def test_relates_to():
    id = generate_test_id("foo", "123")
    actual = generate_test_relates_to(id)
    expected = {"relatesTo": [{"code": "replaces", "target": {"id": id}}]}
    assert actual == expected


def test_document_reference():
    provider_id = NRL_ODS_SUCCESS
    provider_doc_id = "1234"
    actual = generate_test_document_reference(provider_doc_id=provider_doc_id)
    expected = _strip_none(
        {
            "resourceType": "DocumentReference",
            "id": generate_test_id(provider_id, provider_doc_id),
            "type": generate_test_document_type(),
            "subject": generate_test_subject(),
            "custodian": generate_test_custodian(),
            "content": generate_test_content(),
            "relatesTo": None,
            "status": "current",
        }
    )
    assert actual == expected
