import json

from nrlf.core.model import fhir_to_core
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data


def test_fhir_to_core():
    fhir_json = read_test_data("nrlf")
    document = json.dumps(fhir_json)
    api_version = 1

    core_model = fhir_to_core(document=document, api_version=api_version)

    assert core_model.dict() == {
        "id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"},
        "nhs_number": {"S": "9278693472"},
        "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "status": {"S": "current"},
        "version": {"N": api_version},
        "document": {"S": document},
    }
