from typing import Optional

import hypothesis
import pytest
from hypothesis.strategies import builds
from jsonschema import validate
from pydantic import BaseModel, Extra, ValidationError

from feature_tests.common.repository import FeatureTestRepository as Repository
from helpers.aws_session import aws_account_id_from_profile, new_aws_session
from helpers.terraform import get_terraform_json
from nrlf.core.json_schema import (
    _get_contracts_from_db,
    _to_camel_case,
    get_validators_from_db,
    json_schema_to_pydantic_model,
)
from nrlf.core.model import Contract
from nrlf.core.types import DynamoDbClient

JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "additionalProperties": False,
    "title": "Schema for a recording",
    "type": "object",
    "definitions": {
        "artist": {
            "type": "object",
            "properties": {
                "id": {"type": "number"},
                "name": {"type": "string"},
                "functions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["id", "name", "functions"],
        }
    },
    "properties": {
        "id": {"type": "number"},
        "work": {
            "type": "object",
            "properties": {
                "id": {"type": "number"},
                "name": {"type": "string"},
                "composer": {"$ref": "#/definitions/artist"},
            },
        },
        "recording_artists": {
            "type": "array",
            "items": {"$ref": "#/definitions/artist"},
        },
    },
    "required": ["id", "work", "recording_artists"],
}


class Artist(BaseModel):
    id: float
    name: str
    functions: list[str]


class Work(BaseModel):
    id: Optional[float] = None
    name: Optional[str] = None
    composer: Optional[Artist] = None


class SchemaForARecording(BaseModel):
    class Config:
        extra = Extra.forbid

    id: float
    work: Work
    recording_artists: list[Artist]


@hypothesis.given(schema_for_a_recording=builds(SchemaForARecording))
def test_that_validation_of_model_and_schema_are_same(
    schema_for_a_recording: SchemaForARecording,
):
    data = schema_for_a_recording.dict(exclude_none=True)
    validate(instance=data, schema=JSON_SCHEMA)


@hypothesis.given(schema_for_a_recording=builds(SchemaForARecording))
def test_json_schema_to_pydantic_model(schema_for_a_recording: SchemaForARecording):
    NAME = "test123"

    pydantic_model = json_schema_to_pydantic_model(
        json_schema=JSON_SCHEMA, name_override=NAME
    )
    original_schema = SchemaForARecording.schema()
    created_schema = pydantic_model.schema()

    assert created_schema == {**original_schema, "title": NAME}

    data = schema_for_a_recording.dict(exclude_none=True)
    assert pydantic_model(**data) == schema_for_a_recording

    with pytest.raises(ValidationError) as error:
        pydantic_model(bad_data="")

    error.match(f"4 validation errors for {NAME}")
    error.match(f"extra fields not permitted")


@pytest.mark.parametrize(
    "name",
    [
        "this  Is\ta Name",
        "ThisIsAName",
        "thisIsAName",
        "thIs_Is_a_nAme",
        "this-is-a_Name",
    ],
)
def test__to_camel_case(name: str):
    assert _to_camel_case(name=name) == "ThisIsAName"


@pytest.fixture
def repository():
    tf_json = get_terraform_json()
    env = tf_json["account_name"]["value"]
    prefix = tf_json["prefix"]["value"] + "--"
    account_id = aws_account_id_from_profile(env=env)
    session = new_aws_session(account_id=account_id)
    client: DynamoDbClient = session.client("dynamodb")
    return Repository(item_type=Contract, client=client, environment_prefix=prefix)


@pytest.mark.integration
@pytest.mark.parametrize(
    ["system", "value"],
    [
        ("", ""),  # Default case
        ("foo", "bar"),
    ],
)
def test__get_contracts_from_db_returns_latest_versions(
    system: str, value: str, repository: Repository
):
    N_SCHEMA_TYPES = 3
    N_VERSIONS = 10
    MIN_VERSION = 1

    for i_name in range(1, N_SCHEMA_TYPES + 1):
        for v, i in enumerate(reversed(range(MIN_VERSION, N_VERSIONS + MIN_VERSION))):
            repository.create(
                item=Contract(
                    pk=f"C#{system}#{value}",
                    sk=f"V#{i}#name{i_name}",
                    name=f"name{i_name}",
                    version=v + 1,
                    system=system,
                    value=value,
                    json_schema={
                        "$schema": "http://json-schema.org/draft-04/schema#",
                        "additionalProperties": False,
                        "title": f"Base {i_name}",
                        "type": "object",
                    },
                )
            )

    contracts = _get_contracts_from_db(
        repository=repository, system=system, value=value
    )

    assert list(contracts) == [
        Contract(
            pk=f"C#{system}#{value}",
            sk=f"V#{MIN_VERSION}#name1",
            name=f"name1",
            version=N_VERSIONS,
            system=system,
            value=value,
            json_schema={
                "$schema": "http://json-schema.org/draft-04/schema#",
                "additionalProperties": False,
                "title": f"Base 1",
                "type": "object",
            },
        ),
        Contract(
            pk=f"C#{system}#{value}",
            sk=f"V#{MIN_VERSION}#name2",
            name=f"name2",
            version=N_VERSIONS,
            system=system,
            value=value,
            json_schema={
                "$schema": "http://json-schema.org/draft-04/schema#",
                "additionalProperties": False,
                "title": f"Base 2",
                "type": "object",
            },
        ),
        Contract(
            pk=f"C#{system}#{value}",
            sk=f"V#{MIN_VERSION}#name3",
            name=f"name3",
            version=N_VERSIONS,
            system=system,
            value=value,
            json_schema={
                "$schema": "http://json-schema.org/draft-04/schema#",
                "additionalProperties": False,
                "title": f"Base 3",
                "type": "object",
            },
        ),
    ]


@pytest.mark.integration
@pytest.mark.parametrize(
    ["system", "value"],
    [
        ("", ""),  # Default case
        ("foo", "bar"),
    ],
)
def test_get_validators_from_db(system: str, value: str, repository: Repository):
    N_SCHEMA_TYPES = 3
    N_VERSIONS = 10
    MIN_VERSION = 1

    for i_name in range(1, N_SCHEMA_TYPES + 1):
        for v, i in enumerate(reversed(range(MIN_VERSION, N_VERSIONS + MIN_VERSION))):
            repository.create(
                item=Contract(
                    pk=f"C#{system}#{value}",
                    sk=f"V{i}#name{i_name}",
                    name=f"name{i_name}",
                    version=v,
                    system=system,
                    value=value,
                    json_schema={
                        "$schema": "http://json-schema.org/draft-04/schema#",
                        "additionalProperties": False,
                        "title": f"Base {i_name}",
                        "type": "object",
                    },
                )
            )

    validators = get_validators_from_db(
        repository=repository, system=system, value=value
    )
    assert len(validators) == N_SCHEMA_TYPES

    for validator in validators:
        validator({})

    for validator in validators:
        with pytest.raises(ValidationError):
            validator({"foo": "bar"})
