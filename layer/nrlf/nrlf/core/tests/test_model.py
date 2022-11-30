import json
from unittest import mock

import pytest
from nrlf.core.dynamodb_types import convert_value_to_dynamo_format
from nrlf.core.model import (
    ConsumerRequestParams,
    DocumentPointer,
    ProducerRequestParams,
    assert_model_has_only_dynamodb_types,
    create_document_type_tuple,
)
from nrlf.core.transform import (
    create_bundle_from_document_pointers,
    create_document_pointer_from_fhir_json,
    update_document_pointer_from_fhir_json,
)
from nrlf.producer.fhir.r4.model import CodeableConcept, Coding
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data

API_VERSION = 1
TIMESTAMP = "2022-10-18T14:47:22.920Z"


@pytest.mark.parametrize(
    "model",
    [
        DocumentPointer,
    ],
)
def test_assert_model_has_only_dynamodb_types(model):
    assert_model_has_only_dynamodb_types(model)


def test_fields_are_not_all_dynamo_db_type():
    from pydantic import BaseModel

    class TestClass(BaseModel):
        bad_field: str

    with pytest.raises(TypeError) as error:
        assert_model_has_only_dynamodb_types(TestClass)

    (message,) = error.value.args
    assert (
        message
        == "Model contains fields ['bad_field'] that are not of type DynamoDbType"
    )


@mock.patch("nrlf.core.transform.make_timestamp", return_value=TIMESTAMP)
def test_create_document_pointer_from_fhir_json(mock__make_timestamp):
    fhir_json = read_test_data("nrlf")

    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=API_VERSION
    )

    assert core_model.dict() == {
        "id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"},
        "nhs_number": {"S": "9278693472"},
        "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "type": {"S": "https://snomed.info/ict|736253002"},
        "source": {"S": "NRLF"},
        "version": {"N": str(API_VERSION)},
        "document": {"S": json.dumps(fhir_json)},
        "created_on": {"S": TIMESTAMP},
        "updated_on": {"NULL": True},
    }


def test_create_document_type_tuple():
    document_type = CodeableConcept(coding=[Coding(code="foo", system="bar")])
    document_type_tuple = create_document_type_tuple(document_type=document_type)
    assert document_type_tuple == "bar|foo"


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


@mock.patch("nrlf.core.transform.make_timestamp", return_value=TIMESTAMP)
def test_update_document_pointer_from_fhir_json(mock__make_timestamp):
    fhir_json = read_test_data("nrlf")

    core_model = update_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=API_VERSION
    )

    assert core_model.dict() == {
        "id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"},
        "nhs_number": {"S": "9278693472"},
        "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "type": {"S": "https://snomed.info/ict|736253002"},
        "source": {"S": "NRLF"},
        "version": {"N": str(API_VERSION)},
        "document": {"S": json.dumps(fhir_json)},
        "created_on": {"S": TIMESTAMP},
        "updated_on": {"S": TIMESTAMP},
    }


def test_reconstruct_document_pointer_from_db():
    fhir_json = read_test_data("nrlf")

    dynamodb_core_model = {
        "id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"},
        "nhs_number": {"S": "9278693472"},
        "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "type": {"S": "https://snomed.info/ict|736253002"},
        "source": {"S": "NRLF"},
        "version": {"N": str(API_VERSION)},
        "document": {"S": json.dumps(fhir_json)},
        "created_on": {"S": TIMESTAMP},
        "updated_on": {"NULL": True},
    }

    core_model = DocumentPointer(**dynamodb_core_model)
    assert core_model.dict() == {
        "id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890"},
        "nhs_number": {"S": "9278693472"},
        "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "type": {"S": "https://snomed.info/ict|736253002"},
        "source": {"S": "NRLF"},
        "version": {"N": str(API_VERSION)},
        "document": {"S": json.dumps(fhir_json)},
        "created_on": {"S": TIMESTAMP},
        "updated_on": {"NULL": True},
    }


def test_create_bundle_from_multiple_document_pointers():
    fhir_json = read_test_data("nrlf")

    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=API_VERSION
    )
    core_model_2 = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=API_VERSION
    )

    result = create_bundle_from_document_pointers([core_model, core_model_2])

    expected_result = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 2,
        "entry": [
            {
                "resource": {
                    "resourceType": "DocumentReference",
                    "id": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890",
                    "status": "current",
                    "type": {
                        "coding": [
                            {"system": "https://snomed.info/ict", "code": "736253002"}
                        ]
                    },
                    "subject": {
                        "identifier": {
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                            "value": "9278693472",
                        }
                    },
                    "custodian": {
                        "identifier": {
                            "system": "https://fhir.nhs.uk/Id/accredited-system-id",
                            "value": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL",
                        }
                    },
                    "content": [
                        {
                            "attachment": {
                                "contentType": "application/pdf",
                                "url": "https://example.org/my-doc.pdf",
                            }
                        }
                    ],
                }
            },
            {
                "resource": {
                    "resourceType": "DocumentReference",
                    "id": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890",
                    "status": "current",
                    "type": {
                        "coding": [
                            {"system": "https://snomed.info/ict", "code": "736253002"}
                        ]
                    },
                    "subject": {
                        "identifier": {
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                            "value": "9278693472",
                        }
                    },
                    "custodian": {
                        "identifier": {
                            "system": "https://fhir.nhs.uk/Id/accredited-system-id",
                            "value": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL",
                        }
                    },
                    "content": [
                        {
                            "attachment": {
                                "contentType": "application/pdf",
                                "url": "https://example.org/my-doc.pdf",
                            }
                        }
                    ],
                }
            },
        ],
    }

    assert expected_result == result


def test_create_bundle_from_document_pointer():
    fhir_json = read_test_data("nrlf")

    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=API_VERSION
    )

    result = create_bundle_from_document_pointers([core_model])

    expected_result = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 1,
        "entry": [
            {
                "resource": {
                    "resourceType": "DocumentReference",
                    "id": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL|1234567890",
                    "status": "current",
                    "type": {
                        "coding": [
                            {"system": "https://snomed.info/ict", "code": "736253002"}
                        ]
                    },
                    "subject": {
                        "identifier": {
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                            "value": "9278693472",
                        }
                    },
                    "custodian": {
                        "identifier": {
                            "system": "https://fhir.nhs.uk/Id/accredited-system-id",
                            "value": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL",
                        }
                    },
                    "content": [
                        {
                            "attachment": {
                                "contentType": "application/pdf",
                                "url": "https://example.org/my-doc.pdf",
                            }
                        }
                    ],
                }
            }
        ],
    }

    assert expected_result == result


def test_create_bundle_from_document_pointer():

    result = create_bundle_from_document_pointers([])

    expected_result = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 0,
        "entry": [],
    }

    assert expected_result == result


def test_producer_request_params_splits_nhs_id():
    queryParams = {"subject": "https://fhir.nhs.uk/Id/nhs-number|7736959498"}

    request_params = ProducerRequestParams(**queryParams)
    expected = "7736959498"
    assert expected == request_params.nhs_number


def test_producer_request_params_throws_error_on_invalid_nhs_number():
    queryParams = {"subject": "https://fhir.nhs.uk/Id/nhs-number|773695"}

    with pytest.raises(ValueError):
        request_params = ProducerRequestParams(**queryParams)
        request_params.nhs_number


def test_consumer_request_params_splits_nhs_id():
    queryParams = {"subject": "https://fhir.nhs.uk/Id/nhs-number|7736959498"}

    request_params = ConsumerRequestParams(**queryParams)

    expected_nhs_number = "7736959498"

    assert expected_nhs_number == request_params.nhs_number


def test_consumer_request_params_throws_error_on_invalid_nhs_number():
    queryParams = {"subject": "https://fhir.nhs.uk/Id/nhs-number|773695"}

    with pytest.raises(ValueError):
        request_params = ConsumerRequestParams(**queryParams)
        request_params.nhs_number
