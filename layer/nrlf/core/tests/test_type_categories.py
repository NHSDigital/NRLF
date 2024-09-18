import pytest

from layer.nrlf.core.constants import (
    CATEGORY_ATTRIBUTES,
    SYSTEM_SHORT_IDS,
    TYPE_CATEGORIES,
    Categories,
    PointerTypes,
)


@pytest.mark.parametrize("pointer_type", PointerTypes)
def test_pointer_type_has_category(pointer_type):
    assert (
        pointer_type.value in TYPE_CATEGORIES
    ), f"Pointer type {pointer_type.value} has no category"


@pytest.mark.parametrize("pointer_type", PointerTypes)
def test_pointer_types(pointer_type):
    assert (
        pointer_type.coding_system() in SYSTEM_SHORT_IDS
    ), f"Point type system {pointer_type.coding_system()} has no short id"


@pytest.mark.parametrize("category", Categories)
def test_pointer_category_has_types(category):
    assert (
        category.value in TYPE_CATEGORIES.values()
    ), f"Pointer category {category.value} is not used by any type"


@pytest.mark.parametrize("category", Categories)
def test_pointer_category_has_short_code(category):
    assert (
        category.coding_system() in SYSTEM_SHORT_IDS
    ), f"Pointer category system {category.coding_system()} has no short id"


@pytest.mark.parametrize("type", TYPE_CATEGORIES.keys())
def test_type_category_type_is_known(type):
    assert type in PointerTypes.list(), f"Unknown type {type} used in TYPE_CATEGORIES"


@pytest.mark.parametrize("category", TYPE_CATEGORIES.values())
def test_type_category_category_is_known(category):
    assert (
        category in Categories.list()
    ), f"Unknown category {category} used in TYPE_CATEGORIES"


@pytest.mark.parametrize("category", Categories)
def test_category_has_attributes(category):
    assert (
        category.value in CATEGORY_ATTRIBUTES
    ), f"Category {category.value} has no attributes"


@pytest.mark.parametrize("category", Categories)
def test_category_has_required_attributes(category):
    assert (
        category.value in CATEGORY_ATTRIBUTES
    ), f"Category {category.value} has no attributes"
    assert (
        "display" in CATEGORY_ATTRIBUTES[category.value]
    ), f"Category {category.value} has no display attribute"
