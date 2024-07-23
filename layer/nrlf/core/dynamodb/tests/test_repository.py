import pytest

from nrlf.core.constants import PointerTypes
from nrlf.core.dynamodb.repository import _get_sk_ids_for_type


def test_get_sk_ids_for_type_exception_thrown_for_invalid_type():
    with pytest.raises(ValueError) as error:
        _get_sk_ids_for_type("invalid_type")

    assert str(error.value) == "Cannot find category for pointer type: invalid_type"


def test_get_sk_ids_for_type_returns_type_and_category_for_every_type():
    for each in PointerTypes.list():
        category, type = _get_sk_ids_for_type(each)
        assert category and type


def test_get_sk_ids_for_type_exception_thrown_if_new_type_has_no_category():
    pointer_types = PointerTypes.list()
    pointer_types.append("some_pointer_type")
    with pytest.raises(ValueError) as error:
        for each in pointer_types:
            category, type = _get_sk_ids_for_type(each)
            assert category and type

    assert (
        str(error.value) == "Cannot find category for pointer type: some_pointer_type"
    )


# TODO: Add unit tests for Repository Class
