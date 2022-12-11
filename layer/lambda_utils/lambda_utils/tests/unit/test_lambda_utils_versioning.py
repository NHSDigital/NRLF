from pathlib import Path
from unittest import mock

import pytest
from lambda_utils.tests.unit.example_api import index
from lambda_utils.tests.unit.utils import make_aws_event
from lambda_utils.versioning import (
    AcceptHeader,
    VersionException,
    get_largest_possible_version,
    get_versioned_steps,
)
from pydantic import ValidationError

PATH_TO_HERE = Path(__file__).parent


@pytest.mark.parametrize(
    "event, expected_version",
    [
        (make_aws_event(), "1"),
        (make_aws_event(version="2"), "2"),
        (make_aws_event(version="2.0"), "2.0"),
    ],
)
def test_api_version_parsing(event: dict, expected_version: str):
    accept_header = AcceptHeader(**event["headers"])
    assert accept_header.version == expected_version


@pytest.mark.parametrize(
    "event",
    [
        make_aws_event(version="asdf"),
        make_aws_event(version="true"),
        make_aws_event(version="1.0.0"),
        make_aws_event(version="-1.0"),
    ],
)
def test_api_version_parsing_invalid_version(event: dict):
    with pytest.raises(ValidationError):
        AcceptHeader(**event["headers"])


@pytest.mark.parametrize(
    "requested_version,expected_version",
    [
        ("3", "3"),
        ("4", "3"),
        ("5", "3"),
        ("6", "6"),
        ("7", "6"),
        ("8", "6"),
        ("9", "9"),
        ("1000", "9"),
        ("3.0", "3"),
        ("3.5", "3"),
        ("3.9", "3"),
        ("10000.1234", "9"),
    ],
)
def test_largest_possible_version(requested_version: str, expected_version: str):
    handler_versions = {"3": "handler3", "6": "handler6", "9": "handler9"}
    actual_version = get_largest_possible_version(requested_version, handler_versions)
    assert actual_version == expected_version


@pytest.mark.parametrize("requested_version", ["-2", "-1", "0", "1", "2"])
def test_largest_possible_version_error(requested_version: str):
    handler_versions = {"3": "handler3", "6": "handler6", "9": "handler9"}
    with pytest.raises(VersionException) as e:
        get_largest_possible_version(requested_version, handler_versions)
    assert str(e.value) == "Version not supported"


@mock.patch("lambda_utils.versioning.API_ROOT_DIRNAME", "example_api")
def test_get_versioned_steps():
    assert get_versioned_steps(index.__file__) == {
        "0": "v0_steps",
        "1": "v1_steps",
        "3": "v3_steps",
    }
