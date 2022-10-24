import json
from unittest import mock

import pytest
from nrlf.core.model import DYNAMODB_NULL, create_document_type_tuple
from nrlf.core.transform import create_document_pointer_from_fhir_json
from nrlf.producer.fhir.r4.model import CodeableConcept, Coding
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data

API_VERSION = 1
TIMESTAMP = "2022-10-18T14:47:22.920Z"


@mock.patch("nrlf.core.transform.make_timestamp", return_value=TIMESTAMP)
def test_create_document_pointer_from_fhir_json(mock__make_timestamp):
    fhir_json = read_test_data("nrlf")
    dynamodb_json = read_test_data("nrlf-dynamodb-format")

    document = json.dumps(fhir_json)
    core_model = create_document_pointer_from_fhir_json(
        raw_fhir_json=document, api_version=API_VERSION
    )

    assert core_model.dict() == {
        "id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"},
        "nhs_number": {"S": "9278693472"},
        "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "type": {"S": "736253002|https://snomed.info/ict"},
        "source": {"S": "NRLF"},
        "version": {"N": str(API_VERSION)},
        "document": dynamodb_json,
        "created_on": {"S": TIMESTAMP},
        "updated_on": DYNAMODB_NULL,
    }


def test_create_document_type_tuple():
    document_type = CodeableConcept(coding=[Coding(code="foo", system="bar")])
    document_type_tuple = create_document_type_tuple(document_type=document_type)
    assert document_type_tuple == "foo|bar"


@pytest.mark.parametrize(
    "coding",
    [
        [Coding(code="foo", system="bar"), Coding(code="bar", system="foo")],
        [],
    ],
)
def test_create_document_type_tuple_incorrect_size(coding):
    document_type = CodeableConcept(coding=coding)
    with pytest.raises(ValueError):
        create_document_type_tuple(document_type=document_type)
