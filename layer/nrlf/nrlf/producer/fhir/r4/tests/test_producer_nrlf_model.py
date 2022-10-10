import json
from copy import deepcopy
from functools import cache
from pathlib import Path

import pydantic
import pytest
from nrlf.producer.fhir.r4.model import DocumentReference

PATH_TO_HERE = Path(__file__).parent


@cache
def _good_nrlf_document_reference():
    with open(PATH_TO_HERE / "producer_nrlf_fhir.json") as f:
        return json.load(f)


@pytest.fixture()
def good_nrlf_document_reference():
    document_reference = _good_nrlf_document_reference()
    return deepcopy(document_reference)


@pytest.fixture()
def bad_nrlf_document_reference(good_nrlf_document_reference):
    good_nrlf_document_reference["type"] = "an invalid value!"
    return good_nrlf_document_reference


def test_good_nrlf_document_is_valid(good_nrlf_document_reference):
    DocumentReference(**good_nrlf_document_reference)


def test_bad_nrlf_document_is_not_valid(bad_nrlf_document_reference):
    with pytest.raises(pydantic.ValidationError):
        DocumentReference(**bad_nrlf_document_reference)
