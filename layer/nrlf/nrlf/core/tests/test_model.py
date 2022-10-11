import json

from nrlf.core.model import fhir_to_core
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data


def test_fhir_to_core():
    fhir_json = read_test_data("nrlf")
    raw_document = json.dumps(fhir_json)
    api_version = 1

    core_model = fhir_to_core(raw_document=raw_document, api_version=api_version)

    assert core_model.dict() == {
        "id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"},
        "nhs_number": {"S": "9278693472"},
        "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "status": {"S": "current"},
        "version": {"N": api_version},
        "raw_document": {"S": raw_document},
        "validated_document": {
            "S": (
                "{"
                '"resourceType": "DocumentReference", '
                '"masterIdentifier": {"value": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"}, '
                '"status": "current", '
                '"type": {"coding": [{"system": "https://snomed.info/ict", "code": "736253002"}]}, '
                '"subject": {"id": "9278693472"}, '
                '"custodian": {"id": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"}, '
                '"content": [{"attachment": {"contentType": "application/pdf", "url": "https://example.org/my-doc.pdf"}}]'
                "}"
            )
        },
    }
