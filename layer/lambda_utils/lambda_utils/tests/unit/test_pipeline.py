import pytest

from lambda_utils.pipeline import _get_steps
from lambda_utils.versioning import VersionException


@pytest.mark.parametrize(
    "requested_version,handler_version,expected_steps",
    [
        ("1", {"1": "v1_step"}, "v1_step"),
        ("2", {"2": "v2_step"}, "v2_step"),
        ("3", {"2": "v2_step"}, "v2_step"),
    ],
)
def test_get_steps(requested_version: str, handler_version: dict, expected_steps: str):
    steps = _get_steps(requested_version, handler_version)
    assert steps == expected_steps


@pytest.mark.parametrize(
    "requested_version,handler_version",
    [("1", {"2": "v2_step"})],
)
def test_get_steps(requested_version: str, handler_version: dict):
    with pytest.raises(VersionException) as e:
        _get_steps(requested_version, handler_version)
    assert str(e.value) == "Version not supported"
