import pytest

from nrlf.core_pipeline.errors import BadJsonSchema
from nrlf.core_pipeline.json_schema import validate_json_schema

BAD_SCHEMA_TYPE = {
    "type": "object",
    "properties": {
        "name": {"type": "NOT_A_TYPE"},
        "age": {"type": "integer", "minimum": 0},
    },
    "required": ["name", "age"],
    "additionalProperties": False,
}

BAD_SCHEMA_NESTED_TYPE = {
    "type": "object",
    "properties": {
        "people": {
            "type": "array",
            "contains": {
                "type": "object",
                "properties": {
                    "name": {"type": "NOT_A_TYPE"},
                    "age": {"type": "integer", "minimum": 0},
                },
                "required": ["name", "age"],
            },
        }
    },
}

BAD_SCHEMA_BAD_VALUE = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "NOT_A_KEYWORD": 0},
    },
    "required": ["name", "age"],
    "additionalProperties": "NOT_A_VALID_VALUE",
}

BAD_SCHEMA_BAD_CONSTRAINT = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": "NOT_A_NUMBER"},
    },
    "required": ["name", "age"],
    "additionalProperties": False,
}

BAD_SCHEMA_MISSING_SCHEMAS = {
    "oneOf": [
        {"$ref": "#/schemas/schema-one"},
        {"$ref": "#/schemas/schema-two"},
    ],
    "schemas": {},
}


@pytest.mark.parametrize(
    ["json_schema", "error_message"],
    [
        (
            BAD_SCHEMA_TYPE,
            (
                "SchemaError raised from Data Contract 'My Contract' at "
                "'properties.name.type': "
                "'NOT_A_TYPE' is not valid under any of the given schemas"
            ),
        ),
        (
            BAD_SCHEMA_NESTED_TYPE,
            (
                "SchemaError raised from Data Contract 'My Contract' at "
                "'properties.people.contains.properties.name.type': "
                "'NOT_A_TYPE' is not valid under any of the given schemas"
            ),
        ),
        (
            BAD_SCHEMA_BAD_VALUE,
            (
                "SchemaError raised from Data Contract 'My Contract' at "
                "'additionalProperties': "
                "'NOT_A_VALID_VALUE' is not of type 'object', 'boolean'"
            ),
        ),
        (
            BAD_SCHEMA_BAD_CONSTRAINT,
            (
                "SchemaError raised from Data Contract 'My Contract' at "
                "'properties.age.minimum': "
                "'NOT_A_NUMBER' is not of type 'number'"
            ),
        ),
        (
            BAD_SCHEMA_MISSING_SCHEMAS,
            (
                "RefResolutionError raised from Data Contract 'My Contract': "
                "Unresolvable JSON pointer: 'schemas/schema-one'"
            ),
        ),
    ],
)
def test_parse_json_schema_error_bad_schemas(json_schema: dict, error_message: str):
    with pytest.raises(BadJsonSchema) as exception_wrapper:
        validate_json_schema(json_schema=json_schema, contract_name="My Contract")
    assert error_message == str(exception_wrapper.value)
