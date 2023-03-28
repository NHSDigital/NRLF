import json
from unittest import mock

import pytest
from nrlf.core.constants import ID_SEPARATOR, DbPrefix
from nrlf.core.errors import RequestValidationError
from nrlf.core.model import (
    ConsumerRequestParams,
    DocumentPointer,
    PaginatedResponse,
    ProducerRequestParams,
    assert_model_has_only_dynamodb_types,
    create_document_type_tuple,
    key,
)
from nrlf.core.transform import (
    create_bundle_from_paginated_response,
    create_document_pointer_from_fhir_json,
    update_document_pointer_from_fhir_json,
)
from nrlf.producer.fhir.r4.model import CodeableConcept, Coding
from nrlf.producer.fhir.r4.tests.test_producer_nrlf_model import read_test_data

from .data_factory import (
    generate_test_custodian,
    generate_test_document_reference,
    generate_test_subject,
)

API_VERSION = 1
TIMESTAMP = "2022-10-18T14:47:22.920Z"


@pytest.mark.parametrize(
    [
        "provider_id",
        "provider_doc_id",
        "nhs_number",
        "ods_code",
    ],
    [["XX01", "6789", "0730576353", "RX1"], ["AB12", "9876", "2361846292", "JJ0"]],
)
def test_calculated_fields(
    provider_id: str,
    provider_doc_id: str,
    nhs_number: str,
    ods_code: str,
):
    doc = generate_test_document_reference(
        provider_id=provider_id,
        provider_doc_id=provider_doc_id,
        subject=generate_test_subject(nhs_number),
        custodian=generate_test_custodian(ods_code),
    )
    model = create_document_pointer_from_fhir_json(doc, 99)

    assert f"{model.pk}" == key(DbPrefix.DocumentPointer, provider_id, provider_doc_id)
    assert f"{model.sk}" == f"{model.pk}"
    assert f"{model.pk_1}" == key(DbPrefix.Patient, nhs_number)
    assert f"{model.sk_1}" == key(
        DbPrefix.CreatedOn, model.created_on, provider_id, provider_doc_id
    )
    assert f"{model.pk_2}" == key(DbPrefix.Organization, provider_id)
    assert f"{model.sk_2}" == f"{model.sk_2}"


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
        == "Model TestClass contains fields ['bad_field'] that are not of type DynamoDbType"
    )


@mock.patch("nrlf.core.transform.make_timestamp", return_value=TIMESTAMP)
def test_create_document_pointer_from_fhir_json(mock__make_timestamp):
    fhir_json = read_test_data("nrlf")

    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=API_VERSION
    )

    id = "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL-1234567890"
    (_, doc_id) = id.split(ID_SEPARATOR)
    provider_id = "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"
    custodian = "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"
    nhs_number = "9278693472"

    assert core_model.dict() == {
        "pk": {"S": key(DbPrefix.DocumentPointer, provider_id, doc_id)},
        "sk": {"S": key(DbPrefix.DocumentPointer, provider_id, doc_id)},
        "pk_1": {"S": key(DbPrefix.Patient, nhs_number)},
        "sk_1": {"S": key(DbPrefix.CreatedOn, TIMESTAMP, provider_id, doc_id)},
        "pk_2": {"S": key(DbPrefix.Organization, provider_id)},
        "sk_2": {"S": key(DbPrefix.CreatedOn, TIMESTAMP, provider_id, doc_id)},
        "id": {"S": id},
        "nhs_number": {"S": nhs_number},
        "producer_id": {"S": provider_id},
        "custodian": {"S": custodian},
        "type": {"S": "http://snomed.info/sct|736253002"},
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

    actual = core_model.dict()
    expected = {
        **actual,  # we don't test the calculated values here
        "id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL-1234567890"},
        "nhs_number": {"S": "9278693472"},
        "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "custodian": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "type": {"S": "http://snomed.info/sct|736253002"},
        "source": {"S": "NRLF"},
        "version": {"N": str(API_VERSION)},
        "document": {"S": json.dumps(fhir_json)},
        "created_on": {"S": TIMESTAMP},
        "updated_on": {"S": TIMESTAMP},
    }
    assert actual == expected


def test_reconstruct_document_pointer_from_db():
    document = json.dumps(generate_test_document_reference())

    dynamodb_core_model = {
        "id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL-1234567890"},
        "nhs_number": {"S": "9278693472"},
        "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "custodian": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "type": {"S": "http://snomed.info/sct|736253002"},
        "source": {"S": "NRLF"},
        "version": {"N": str(API_VERSION)},
        "document": {"S": document},
        "created_on": {"S": TIMESTAMP},
        "updated_on": {"NULL": True},
    }

    core_model = DocumentPointer(**dynamodb_core_model)

    actual = core_model.dict()
    expected = {
        **actual,  # we don't test the calculated values here
        "id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL-1234567890"},
        "nhs_number": {"S": "9278693472"},
        "producer_id": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "custodian": {"S": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL"},
        "type": {"S": "http://snomed.info/sct|736253002"},
        "source": {"S": "NRLF"},
        "version": {"N": str(API_VERSION)},
        "document": {"S": document},
        "created_on": {"S": TIMESTAMP},
        "updated_on": {"NULL": True},
    }
    assert actual == expected


def test_create_bundle_from_paginated_response_returns_populated_bundle_of_2():
    fhir_json = read_test_data("nrlf")

    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=API_VERSION
    )
    core_model_2 = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=API_VERSION
    )

    paginated_response = PaginatedResponse(document_pointers=[core_model, core_model_2])

    result = create_bundle_from_paginated_response(paginated_response)

    expected_result = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 2,
        "entry": [
            {
                "resource": {
                    "resourceType": "DocumentReference",
                    "id": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL-1234567890",
                    "status": "current",
                    "type": {
                        "coding": [
                            {"system": "http://snomed.info/sct", "code": "736253002"}
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
                    "id": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL-1234567890",
                    "status": "current",
                    "type": {
                        "coding": [
                            {"system": "http://snomed.info/sct", "code": "736253002"}
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


def test_create_bundle_from_paginated_response_returns_populated_bundle_of_1():
    fhir_json = read_test_data("nrlf")

    core_model = create_document_pointer_from_fhir_json(
        fhir_json=fhir_json, api_version=API_VERSION
    )

    paginated_response = PaginatedResponse(document_pointers=[core_model])

    result = create_bundle_from_paginated_response(paginated_response)

    expected_result = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 1,
        "entry": [
            {
                "resource": {
                    "resourceType": "DocumentReference",
                    "id": "ACUTE MENTAL HEALTH UNIT & DAY HOSPITAL-1234567890",
                    "status": "current",
                    "type": {
                        "coding": [
                            {"system": "http://snomed.info/sct", "code": "736253002"}
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


def test_create_bundle_from_paginated_response_returns_unpopulated_bundle():

    paginated_response = PaginatedResponse(document_pointers=[])
    result = create_bundle_from_paginated_response(paginated_response)

    expected_result = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 0,
        "entry": [],
    }

    assert expected_result == result


def test_producer_request_params_splits_nhs_id():
    queryParams = {"subject.identifier": "https://fhir.nhs.uk/Id/nhs-number|7736959498"}

    request_params = ProducerRequestParams(**queryParams)
    expected = "7736959498"
    assert expected == request_params.nhs_number


def test_consumer_request_params_splits_nhs_id():
    queryParams = {"subject.identifier": "https://fhir.nhs.uk/Id/nhs-number|7736959498"}

    request_params = ConsumerRequestParams(**queryParams)

    expected_nhs_number = "7736959498"

    assert expected_nhs_number == request_params.nhs_number
