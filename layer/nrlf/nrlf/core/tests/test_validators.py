from unittest import mock

import pytest
from nrlf.core.transform import make_timestamp
from nrlf.core.validators import (
    requesting_application_is_not_authorised,
    validate_nhs_number,
    validate_source,
    validate_timestamp,
    validate_tuple,
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


@mock.patch("nrlf.core.validators.VALID_SOURCES", {"foo", "bar"})
@pytest.mark.parametrize(
    ["source", "expected_outcome"],
    (["foo", True], ["bar", True], ["baz", False]),
)
def test_validate_source(source, expected_outcome):
    outcome = True
    try:
        validate_source(source=source)
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
    timestamp = make_timestamp()
    validate_timestamp(timestamp)


@pytest.mark.parametrize(
    ["requesting_application_id", "authenticated_application_id", "expected_outcome"],
    (
        ["SCRa", "SCRa", False],
        ["SCRa", "APIM", True],
        ["APIM", "SCRA", True],
        ["SCRA", 4, True],
    ),
)
def test_requesting_application_is_not_authorised(
    requesting_application_id, authenticated_application_id, expected_outcome
):
    result = requesting_application_is_not_authorised(
        requesting_application_id, authenticated_application_id
    )

    assert result == expected_outcome
