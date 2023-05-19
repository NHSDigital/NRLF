import json
from copy import deepcopy
from pathlib import Path

import pydantic
import pytest

from nrlf.producer.fhir.r4.model import DocumentReference

PATH_TO_TEST_DATA = Path(__file__).parent / "data"
TEST_DATA_RELATIVE_PATHS = ["nrlf", "www.hl7.org/fhir/R4", "www.hl7.org/fhir/R4B"]


def read_test_data(relative_path: str):
    with open(
        PATH_TO_TEST_DATA / relative_path / "documentreference-example.json"
    ) as f:
        return json.load(f)


@pytest.mark.parametrize("relative_path", TEST_DATA_RELATIVE_PATHS)
def test_good_nrlf_document_is_valid(relative_path):
    document_reference = read_test_data(relative_path=relative_path)
    DocumentReference(**document_reference)


@pytest.mark.parametrize("relative_path", TEST_DATA_RELATIVE_PATHS)
def test_bad_nrlf_document_is_valid(relative_path):
    document_reference = deepcopy(read_test_data(relative_path=relative_path))
    document_reference["type"] = "an invalid value!"
    with pytest.raises(pydantic.ValidationError):
        DocumentReference(**document_reference)
