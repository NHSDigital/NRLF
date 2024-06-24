import json

import pytest
from freezegun import freeze_time

from nrlf.core.constants import PointerTypes
from nrlf.core.dynamodb.model import DocumentPointer, DynamoDBModel
from nrlf.core.utils import create_fhir_instant
from nrlf.producer.fhir.r4.model import DocumentReference
from nrlf.tests.data import load_document_reference, load_document_reference_json


def test_dynamodb_model_init():
    model = DynamoDBModel()

    assert model.kebab() == "dynamo-d-b-model"
    assert model.public_alias() == "DynamoDBModel"
    assert model._from_dynamo is False

    # Check _from_dynamo is a private attribute
    assert model.dict() == {}


def test_dynamodb_model_init_from_dynamo():
    model = DynamoDBModel(_from_dynamo=True)
    assert model.kebab() == "dynamo-d-b-model"
    assert model.public_alias() == "DynamoDBModel"
    assert model._from_dynamo is True

    # Check _from_dynamo is a private attribute
    assert model.dict() == {}


@freeze_time("2024-01-01")
def test_document_pointer_init():
    model = DocumentPointer(
        id="X26-999999-999999-99999999",
        nhs_number="9999999999",
        custodian="X26",
        author="X26",
        master_identifier="1111-11111-111111",
        producer_id=None,  # type: ignore
        type="http://snomed.info/sct|123456789",
        type_id="SCT-123456789",
        category="http://snomed.info/sct|987654321",
        category_id="SCT-987654321",
        source="NRLF",
        version=1,
        document="document",
        created_on=create_fhir_instant(),
        document_id="document_id",
    )

    assert model.kebab() == "document-pointer"
    assert model.public_alias() == "DocumentReference"
    assert model._from_dynamo is False

    assert model.dict() == {
        "id": "X26-999999-999999-99999999",
        "nhs_number": "9999999999",
        "custodian": "X26",
        "custodian_suffix": None,
        "author": "X26",
        "producer_id": "X26",
        "type": "http://snomed.info/sct|123456789",
        "type_id": "SCT-123456789",
        "category": "http://snomed.info/sct|987654321",
        "category_id": "SCT-987654321",
        "master_identifier": "1111-11111-111111",
        "source": "NRLF",
        "version": 1,
        "document": "document",
        "created_on": "2024-01-01T00:00:00.000Z",
        "pk": "D#X26-999999-999999-99999999",
        "sk": "D#X26-999999-999999-99999999",
        "patient_key": "P#9999999999",
        "patient_sort": "C#SCT-987654321#T#SCT-123456789#CO#2024-01-01T00:00:00.000Z#D#X26-999999-999999-99999999",
        "masterid_key": "O#X26#MI#1111-11111-111111",
        "schemas": [],
        "updated_on": None,
    }


@freeze_time("2024-01-01")
def test_document_pointer_from_document_reference_valid():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    model = DocumentPointer.from_document_reference(doc_ref)

    model_data = model.dict()
    document = model_data.pop("document")

    assert model_data == {
        "created_on": "2024-01-01T00:00:00.000Z",
        "custodian": "Y05868",
        "custodian_suffix": None,
        "author": "Y05868",
        "id": "Y05868-99999-99999-999999",
        "master_identifier": None,
        "nhs_number": "6700028191",
        "producer_id": "Y05868",
        "schemas": [],
        "source": "NRLF",
        "type": PointerTypes.MENTAL_HEALTH_PLAN.value,
        "type_id": "SCT-736253002",
        "category": "http://snomed.info/sct|734163000",
        "category_id": "SCT-734163000",
        "updated_on": None,
        "version": 1,
        "pk": "D#Y05868-99999-99999-999999",
        "sk": "D#Y05868-99999-99999-999999",
        "patient_key": "P#6700028191",
        "patient_sort": "C#SCT-734163000#T#SCT-736253002#CO#2024-01-01T00:00:00.000Z#D#Y05868-99999-99999-999999",
    }

    assert json.loads(document) == doc_ref.dict(exclude_none=True)


def test_document_pointer_from_document_reference_valid_with_created_on():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    model = DocumentPointer.from_document_reference(
        doc_ref, created_on="2024-02-02T12:34:56.000Z"
    )

    model_data = model.dict()
    document = model_data.pop("document")

    assert model_data == {
        "created_on": "2024-02-02T12:34:56.000Z",
        "custodian": "Y05868",
        "custodian_suffix": None,
        "author": "Y05868",
        "id": "Y05868-99999-99999-999999",
        "master_identifier": None,
        "nhs_number": "6700028191",
        "producer_id": "Y05868",
        "schemas": [],
        "source": "NRLF",
        "type": PointerTypes.MENTAL_HEALTH_PLAN.value,
        "type_id": "SCT-736253002",
        "category": "http://snomed.info/sct|734163000",
        "category_id": "SCT-734163000",
        "updated_on": None,
        "version": 1,
        "pk": "D#Y05868-99999-99999-999999",
        "sk": "D#Y05868-99999-99999-999999",
        "patient_key": "P#6700028191",
        "patient_sort": "C#SCT-734163000#T#SCT-736253002#CO#2024-02-02T12:34:56.000Z#D#Y05868-99999-99999-999999",
    }

    assert json.loads(document) == doc_ref.dict(exclude_none=True)


def test_document_pointer_from_document_reference_invalid():
    doc_ref = load_document_reference("Y05868-736253002-Valid")
    doc_ref.type = None

    # We should have already validated these fields are present by this point,
    # so allow directly raising the AttributeError to cause an error.
    with pytest.raises(AttributeError) as error:
        DocumentPointer.from_document_reference(doc_ref)

    assert str(error.value) == "'NoneType' object has no attribute 'coding'"


def test_document_pointer_from_document_reference_multiple_types():
    doc_ref_data = load_document_reference_json("Y05868-736253002-Valid")
    doc_ref = DocumentReference.parse_obj(
        {
            **doc_ref_data,
            "type": {
                "coding": [
                    {"system": "http://snomed.info/sct", "code": "123456789"},
                    {"system": "http://snomed.info/sct", "code": "987654321"},
                ]
            },
        }
    )

    with pytest.raises(ValueError) as error:
        DocumentPointer.from_document_reference(doc_ref)

    assert (
        str(error.value) == "DocumentReference.type.coding must have exactly one item"
    )


def test_document_pointer_extract_custodian_suffix_no_suffix():
    values = {"custodian": "X26", "custodian_suffix": None}

    assert DocumentPointer.extract_custodian_suffix(values) == {
        "custodian": "X26",
        "custodian_suffix": None,
    }


def test_document_pointer_extract_custodian_suffix_suffix():
    values = {"custodian": "X26.001", "custodian_suffix": None}

    assert DocumentPointer.extract_custodian_suffix(values) == {
        "custodian": "X26",
        "custodian_suffix": "001",
    }


def test_document_pointer_extract_custodian_suffix_existing_suffix():
    values = {"custodian": "X26", "custodian_suffix": "001"}

    assert DocumentPointer.extract_custodian_suffix(values) == {
        "custodian": "X26",
        "custodian_suffix": "001",
    }


def test_document_pointer_extract_custodian_suffix_multiple_suffix():
    values = {"custodian": "X26.001.002", "custodian_suffix": None}

    assert DocumentPointer.extract_custodian_suffix(values) == {
        "custodian": "X26.001.002",
        "custodian_suffix": None,
    }


def test_document_pointer_inject_producer_id():
    values = {"id": "X26-999999-999999-99999999", "producer_id": None}

    assert DocumentPointer.inject_producer_id(values) == {
        "id": "X26-999999-999999-99999999",
        "producer_id": "X26",
        "document_id": "999999-999999-99999999",
    }


def test_document_pointer_inject_producer_id_existing_producer_id():
    values = {"id": "X26-999999-999999-99999999", "producer_id": "X26"}

    with pytest.raises(ValueError) as error:
        DocumentPointer.inject_producer_id(values)

    assert (
        str(error.value)
        == "producer_id should not be passed to DocumentPointer; it will be extracted from id."
    )


def test_document_pointer_inject_producer_id_existing_producer_id_from_dynamo():
    values = {
        "_from_dynamo": True,
        "id": "X26-999999-999999-9999999",
        "producer_id": "X26",
    }

    assert DocumentPointer.inject_producer_id(values) == {
        "_from_dynamo": True,
        "id": "X26-999999-999999-9999999",
        "producer_id": "X26",
        "document_id": "999999-999999-9999999",
    }


@pytest.mark.parametrize(
    "id_",
    [
        "X26-999999-999999-99999999",
        "X26.001-999999-999999-99999999",
        "Y05868-99999-99999-999999",
        "ABC-123",
        "123-ABC",
        "abc-def",
        "x-y-z",
    ],
)
def test_validate_id(id_):
    assert DocumentPointer.validate_id(id_) == id_


@pytest.mark.parametrize(
    "id_",
    [
        "-X26-999999-999999-99999999",
        "X26_999999_999999_99999999",
    ],
)
def test_validate_id_invalid(id_):
    with pytest.raises(ValueError):
        DocumentPointer.validate_id(id_)
