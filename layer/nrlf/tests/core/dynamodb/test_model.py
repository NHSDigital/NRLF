import json
from datetime import datetime, timezone

import pytest
from freezegun import freeze_time
from tests.utilities import load_json_file

from nrlf.core.dynamodb.model import DocumentPointer, DynamoDBModel
from nrlf.producer.fhir.r4.model import DocumentReference


def test_DynamoDBModel_init():
    model = DynamoDBModel()

    assert model.kebab() == "dynamo-d-b-model"
    assert model.public_alias() == "DynamoDBModel"
    assert model._from_dynamo is False

    # Check _from_dynamo is a private attribute
    assert model.dict() == {}


def test_DynamoDBModel_init_from_dynamo():
    model = DynamoDBModel(_from_dynamo=True)
    assert model.kebab() == "dynamo-d-b-model"
    assert model.public_alias() == "DynamoDBModel"
    assert model._from_dynamo is True

    # Check _from_dynamo is a private attribute
    assert model.dict() == {}


@freeze_time("2024-01-01")
def test_DocumentPointer_init():
    model = DocumentPointer(
        id="X26-999999-999999-99999999",
        nhs_number="9999999999",
        custodian="X26",
        producer_id=None,  # type: ignore
        type="http://snomed.info/sct|123456789",
        source="NRLF",
        version=1,
        document="document",
        created_on=datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds")
        + "Z",
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
        "producer_id": "X26",
        "type": "http://snomed.info/sct|123456789",
        "source": "NRLF",
        "version": 1,
        "document": "document",
        "created_on": "2024-01-01T00:00:00.000+00:00Z",
        "pk": "D#X26#999999-999999-99999999",
        "sk": "D#X26#999999-999999-99999999",
        "pk_1": "P#9999999999",
        "sk_1": "CO#2024-01-01T00:00:00.000+00:00Z#X26#999999-999999-99999999",
        "pk_2": "O#X26",
        "sk_2": "CO#2024-01-01T00:00:00.000+00:00Z#X26#999999-999999-99999999",
        "schemas": [],
        "updated_on": None,
    }


@freeze_time("2024-01-01")
def test_DocumentPointer_from_document_reference_valid():
    doc_ref_data = load_json_file("ValidDocumentReference.json")
    doc_ref = DocumentReference.parse_obj(doc_ref_data)

    model = DocumentPointer.from_document_reference(doc_ref)

    model_data = model.dict()
    document = model_data.pop("document")

    assert model_data == {
        "created_on": "2024-01-01T00:00:00.000+00:00Z",
        "custodian": "Y05868",
        "custodian_suffix": None,
        "id": "Y05868-99999-99999-999999",
        "nhs_number": "6700028191",
        "producer_id": "Y05868",
        "schemas": [],
        "source": "NRLF",
        "type": "http://snomed.info/sct|736253002",
        "updated_on": None,
        "version": 1,
        "pk": "D#Y05868#99999-99999-999999",
        "sk": "D#Y05868#99999-99999-999999",
        "pk_1": "P#6700028191",
        "sk_1": "CO#2024-01-01T00:00:00.000+00:00Z#Y05868#99999-99999-999999",
        "pk_2": "O#Y05868",
        "sk_2": "CO#2024-01-01T00:00:00.000+00:00Z#Y05868#99999-99999-999999",
    }

    assert json.loads(document) == doc_ref.dict(exclude_none=True)


def test_DocumentPointer_from_document_reference_valid_with_created_on():
    doc_ref_data = load_json_file("ValidDocumentReference.json")
    doc_ref = DocumentReference.parse_obj(doc_ref_data)

    model = DocumentPointer.from_document_reference(
        doc_ref, created_on="2024-02-02T12:34:56.000+00:00Z"
    )

    model_data = model.dict()
    document = model_data.pop("document")

    assert model_data == {
        "created_on": "2024-02-02T12:34:56.000+00:00Z",
        "custodian": "Y05868",
        "custodian_suffix": None,
        "id": "Y05868-99999-99999-999999",
        "nhs_number": "6700028191",
        "producer_id": "Y05868",
        "schemas": [],
        "source": "NRLF",
        "type": "http://snomed.info/sct|736253002",
        "updated_on": None,
        "version": 1,
        "pk": "D#Y05868#99999-99999-999999",
        "sk": "D#Y05868#99999-99999-999999",
        "pk_1": "P#6700028191",
        "sk_1": "CO#2024-02-02T12:34:56.000+00:00Z#Y05868#99999-99999-999999",
        "pk_2": "O#Y05868",
        "sk_2": "CO#2024-02-02T12:34:56.000+00:00Z#Y05868#99999-99999-999999",
    }

    assert json.loads(document) == doc_ref.dict(exclude_none=True)


def test_DocumentPointer_from_document_reference_invalid():
    doc_ref_data = load_json_file("ValidDocumentReference.json")
    doc_ref = DocumentReference.parse_obj(doc_ref_data)
    doc_ref.type = None

    # We should have already validated these fields are present by this point,
    # so allow directly raising the AttributeError to cause an error.
    with pytest.raises(AttributeError) as error:
        DocumentPointer.from_document_reference(doc_ref)

    assert str(error.value) == "'NoneType' object has no attribute 'coding'"


def test_DocumentPointer_from_document_reference_multiple_types():
    doc_ref_data = load_json_file("ValidDocumentReference.json")
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


def test_DocumentPointer_extract_custodian_suffix_no_suffix():
    values = {"custodian": "X26", "custodian_suffix": None}

    assert DocumentPointer.extract_custodian_suffix(values) == {
        "custodian": "X26",
        "custodian_suffix": None,
    }


def test_DocumentPointer_extract_custodian_suffix_suffix():
    values = {"custodian": "X26.001", "custodian_suffix": None}

    assert DocumentPointer.extract_custodian_suffix(values) == {
        "custodian": "X26",
        "custodian_suffix": "001",
    }


def test_DocumentPointer_extract_custodian_suffix_existing_suffix():
    values = {"custodian": "X26", "custodian_suffix": "001"}

    assert DocumentPointer.extract_custodian_suffix(values) == {
        "custodian": "X26",
        "custodian_suffix": "001",
    }


def test_DocumentPointer_extract_custodian_suffix_multiple_suffix():
    values = {"custodian": "X26.001.002", "custodian_suffix": None}

    assert DocumentPointer.extract_custodian_suffix(values) == {
        "custodian": "X26.001.002",
        "custodian_suffix": None,
    }


def test_DocumentPointer_inject_producer_id():
    values = {"id": "X26-999999-999999-99999999", "producer_id": None}

    assert DocumentPointer.inject_producer_id(values) == {
        "id": "X26-999999-999999-99999999",
        "producer_id": "X26",
        "document_id": "999999-999999-99999999",
    }


def test_DocumentPointer_inject_producer_id_existing_producer_id():
    values = {"id": "X26-999999-999999-99999999", "producer_id": "X26"}

    with pytest.raises(ValueError) as error:
        DocumentPointer.inject_producer_id(values)

    assert (
        str(error.value)
        == "producer_id should not be passed to DocumentPointer; it will be extracted from id."
    )


def test_DocumentPointer_inject_producer_id_existing_producer_id_from_dynamo():
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
