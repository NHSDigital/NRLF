import pytest
from nrlf.core.model import DynamoDbType


@pytest.mark.parametrize(
    ["python_type", "value", "expected"],
    (
        [str, "foo", {"S": "foo"}],
        [int, 1, {"N": 1}],
        [float, 2.3, {"N": 2.3}],
    ),
)
def test_dynamodb_type(python_type, value, expected):
    assert DynamoDbType[python_type](value=value).value == expected
