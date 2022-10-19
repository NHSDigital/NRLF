from typing import List
import pytest
from layer.lambda_utils.lambda_utils.versioning import (
    AcceptHeader,
    VersionException,
    get_largest_possible_version,
    get_steps
)


def test_api_version_parsing():
    event = {"headers": {"Accept": "version=1", "test": "test"}}
    accept_header = AcceptHeader(event)
    assert accept_header.version == "1"


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
        _actual_version = get_largest_possible_version(
            requested_version, handler_versions
        )
    assert str(e.value) == "Version not supported"

@pytest.mark.parametrize(
    "requested_version,handler_version,expected_steps",
    [
        ("1", {"1": "v1_step"}, "v1_step"),
        ("2", {"2": "v2_step"}, "v2_step"),
        ("3", {"2": "v2_step"}, "v2_step")
    ],
)
def test_get_steps(requested_version: str, handler_version: dict, expected_steps: str):
    steps = get_steps(requested_version, handler_version)
    assert steps == expected_steps

@pytest.mark.parametrize(
    "requested_version,handler_version,expected_steps",
    [
        ("1", {"2": "v2_step"}, "v2_step")
    ],
)
def test_get_steps(requested_version: str, handler_version: dict, expected_steps: str):
    with pytest.raises(VersionException) as e:
        steps = get_steps(requested_version, handler_version)
    assert str(e.value) == "Version not supported"
