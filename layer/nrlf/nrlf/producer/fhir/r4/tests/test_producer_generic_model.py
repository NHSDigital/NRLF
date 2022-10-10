from copy import deepcopy
import pydantic
import pytest
import requests
from functools import cache

from nrlf.producer.fhir.r4.model import DocumentReference

GOOD_DOCUMENT_REFERENCE_URL = "https://www.hl7.org/fhir/documentreference-example.json"


@cache
def _good_generic_document_reference():
    response = requests.get(GOOD_DOCUMENT_REFERENCE_URL)
    response.raise_for_status()
    return response.json()


@pytest.fixture()
def good_generic_document_reference():
    document_reference = _good_generic_document_reference()
    return deepcopy(document_reference)


@pytest.fixture()
def bad_generic_document_reference(good_generic_document_reference):
    good_generic_document_reference["type"] = "an invalid value!"
    return good_generic_document_reference


def test_good_generic_document_is_valid(good_generic_document_reference):
    DocumentReference(**good_generic_document_reference)


def test_bad_generic_document_is_not_valid(bad_generic_document_reference):
    with pytest.raises(pydantic.ValidationError):
        DocumentReference(**bad_generic_document_reference)
