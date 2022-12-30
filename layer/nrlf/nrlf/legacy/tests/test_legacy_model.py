import json
from functools import cache
from pathlib import Path

import pytest

from nrlf.core.transform import (
    _create_fhir_model_from_legacy_model,
    _create_legacy_model_from_legacy_json,
    _strip_empty_json_paths,
    create_document_pointer_from_legacy_json,
)
from nrlf.legacy.model import LegacyDocumentPointer

PATH_TO_TEST_DATA = Path(__file__).parent / "data"
LEGACY_TEST_DATA_FILENAMES = [
    "legacy_document_1.json",
    "legacy_document_2.json",
    "legacy_document_3.json",
]
NHS_NUMBER = "3006500369"
PRODUCER_ID = "producer_123"


@cache
def read_test_data(filename: str, _type: str = ""):
    filename = filename.replace("legacy_document", f"legacy_document{_type}")
    with open(PATH_TO_TEST_DATA / filename) as f:
        return json.load(f)


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            {"foo": "bar", "baz": [{"spam": None, "eggs": ""}, {"bam": "wap"}]},
            {"foo": "bar", "baz": [{"bam": "wap"}]},
        ),
        (
            {"foo": None, "baz": [{"spam": "eggs"}, {"bam": ""}]},
            {"baz": [{"spam": "eggs"}]},
        ),
        (
            {"foo": {"spam": None}},
            None,
        ),
    ],
)
def test__strip_empty_json_paths(input, expected):
    assert _strip_empty_json_paths(input) == expected


@pytest.mark.parametrize("filename", LEGACY_TEST_DATA_FILENAMES)
def test_legacy_document_pointer_is_valid(filename):
    legacy_json = read_test_data(filename)
    LegacyDocumentPointer(**legacy_json)


@pytest.mark.parametrize("filename", LEGACY_TEST_DATA_FILENAMES)
def test_create_document_pointer_from_legacy_json(filename):
    legacy_json = read_test_data(filename)
    legacy_json_as_core = read_test_data(filename, _type="_as_core")
    core_model = create_document_pointer_from_legacy_json(
        legacy_json=legacy_json, nhs_number=NHS_NUMBER, producer_id=PRODUCER_ID
    )
    core_json = core_model.super_dict()
    core_json["document"] = "<<mocked out>>"  # For readability

    assert core_json == legacy_json_as_core


@pytest.mark.parametrize("filename", LEGACY_TEST_DATA_FILENAMES)
def test__create_fhir_model_from_legacy_model(filename):
    legacy_json = read_test_data(filename)
    legacy_json_as_fhir = read_test_data(filename, _type="_as_fhir")

    legacy_model = _create_legacy_model_from_legacy_json(legacy_json=legacy_json)
    fhir_model = _create_fhir_model_from_legacy_model(
        legacy_model=legacy_model, nhs_number=NHS_NUMBER, producer_id=PRODUCER_ID
    )
    assert fhir_model.dict(exclude_none=True) == legacy_json_as_fhir
