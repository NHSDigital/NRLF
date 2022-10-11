import pytest

from nrlf.core.validators import (
    validate_document,
    validate_id,
    validate_nhs_number,
    validate_status,
)


@pytest.mark.parametrize(
    ["id", "producer_id", "expected_outcome"],
    (
        ["foo|bar", "foo", True],
        ["foo|bar", "bar", False],
        ["foo|bar", "baz", False],
    ),
)
def test_validate_id(id, producer_id, expected_outcome):
    outcome = True
    try:
        validate_id(id=id, producer_id=producer_id)
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
        ["superseded", True],
        ["entered-in-error", True],
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
    ["document", "expected_outcome"],
    (
        ['{"foo": "bar"}', True],
        ["foo", False],
    ),
)
def test_validate_document(document, expected_outcome):
    outcome = True
    try:
        validate_document(document=document)
    except ValueError:
        outcome = False
    assert expected_outcome == outcome
