import pytest

from nrlf.core.validators import (
    validate_tuple,
    validate_nhs_number,
    validate_status,
    validate_timestamp,
    make_timestamp,
)


@pytest.mark.parametrize(
    ["tuple", "expected_outcome"],
    (
        ["foo|bar", True],
        ["foo|bar|baz", False],
        ["foo", False],
    ),
)
def test_validate_tuple(tuple, expected_outcome):
    outcome = True
    try:
        validate_tuple(tuple=tuple)
    except ValueError:
        outcome = False
    assert expected_outcome == outcome


@pytest.mark.parametrize(
    ["nhs_number", "expected_outcome"],
    (
        ["2965487948", True],
        ["foo", False],
        ["123456", False],
    ),
)
def test_validate_nhs_number(nhs_number, expected_outcome):
    outcome = True
    try:
        validate_nhs_number(nhs_number=nhs_number)
    except ValueError:
        outcome = False
    assert expected_outcome == outcome


@pytest.mark.parametrize(
    ["status", "expected_outcome"],
    (
        ["current", True],
        ["foo", False],
    ),
)
def test_validate_status(status, expected_outcome):
    outcome = True
    try:
        validate_status(status=status)
    except ValueError:
        outcome = False
    assert expected_outcome == outcome


@pytest.mark.parametrize(
    ["date", "expected_outcome"],
    (
        ["2022-10-18T14:47:22.920Z", True],
        ["foo", False],
    ),
)
def test_validate_timestamp(date, expected_outcome):
    outcome = True
    try:
        validate_timestamp(date=date)
    except ValueError:
        outcome = False
    assert expected_outcome == outcome


def test_make_timestamp():
    from datetime import datetime

    timestamp = make_timestamp()
    validate_timestamp(timestamp)
