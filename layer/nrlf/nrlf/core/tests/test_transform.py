import pytest
from nrlf.core.errors import FhirValidationError
from nrlf.core.transform import validate_no_extra_fields
from pydantic import BaseModel


class Foo(BaseModel):
    spam: str
    eggs: int


def test_validate_no_extra_fields_success():
    json_without_extra_fields = {"spam": "SPAM", "eggs": 123}
    json_as_model = Foo(**json_without_extra_fields)
    validate_no_extra_fields(
        json_as_model.dict(exclude_none=True), json_without_extra_fields
    )


def test_validate_no_extra_fields_failure():
    json_with_extra_fields = {"spam": "SPAM", "eggs": 123, "bar": "BAR"}
    json_as_model = Foo(**json_with_extra_fields)
    with pytest.raises(FhirValidationError):
        validate_no_extra_fields(
            json_as_model.dict(exclude_none=True), json_with_extra_fields
        )
