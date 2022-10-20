from pathlib import Path
from unittest import mock
import pytest
from lambda_utils.versioning import (
    AcceptHeader,
    VersionException,
    get_largest_possible_version,
    get_steps,
    get_versioned_steps,
)
from lambda_utils.tests.unit.utils import make_aws_event
from lambda_utils.tests.unit.example_api import index

PATH_TO_HERE = Path(__file__).parent


@pytest.mark.parametrize(
    "event, expected_version",
    [(make_aws_event(), "1"), (make_aws_event(version="2"), "2")],
)
def test_api_version_parsing(event: dict, expected_version: str):
    accept_header = AcceptHeader(event)
    assert accept_header.version == expected_version


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


@pytest.mark.parametrize(
    "requested_version,handler_version,expected_steps",
    [
        ("1", {"1": "v1_step"}, "v1_step"),
        ("2", {"2": "v2_step"}, "v2_step"),
        ("3", {"2": "v2_step"}, "v2_step"),
    ],
)
def test_get_steps(requested_version: str, handler_version: dict, expected_steps: str):
    steps = get_steps(requested_version, handler_version)
    assert steps == expected_steps


@pytest.mark.parametrize(
    "requested_version,handler_version",
    [("1", {"2": "v2_step"})],
)
def test_get_steps(requested_version: str, handler_version: dict):
    with pytest.raises(VersionException) as e:
        get_steps(requested_version, handler_version)
    assert str(e.value) == "Version not supported"


@mock.patch("lambda_utils.versioning.API_ROOT_DIRNAME", "example_api")
def test_get_versioned_steps():
    assert get_versioned_steps(index.__file__) == {
        "0": "v0_steps",
        "1": "v1_steps",
        "3": "v3_steps",
    }
