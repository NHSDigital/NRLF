import random
from typing import Optional

import hypothesis
import pytest
from hypothesis.strategies import builds
from pydantic import BaseModel, Extra

from feature_tests.common.repository import FeatureTestRepository as Repository
from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json
from nrlf.core.constants import DbPrefix
from nrlf.core.json_schema import (
    JsonSchemaValidationError,
    get_contracts_from_db,
    validate_against_json_schema,
    validate_json_schema,
)
from nrlf.core.model import Contract, key
from nrlf.core.types import DynamoDbClient

# The following are taken from
# https://nhsd-confluence.digital.nhs.uk/pages/viewpage.action?spaceKey=CLP&title=NRLF+-+Document+Type+Contracts

SSP_JSON_SCHEMA = {
    "oneOf": [
        {"$ref": "#/schemas/has-no-ssp-content"},
        {"$ref": "#/schemas/has-ssp-content-and-asid-author"},
    ],
    "schemas": {
        "has-no-ssp-content": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "pattern": r"^(?!ssp:\/\/).+"}
                        },
                    },
                }
            },
        },
        "has-ssp-content-and-asid-author": {
            "type": "object",
            "properties": {
                "author": {
                    "type": "array",
                    "contains": {
                        "type": "object",
                        "properties": {
                            "system": {
                                "type": "string",
                                "enum": ["https://fhir.nhs.uk/Id/accredited-system-id"],
                            }
                        },
                    },
                },
                "content": {
                    "type": "array",
                    "contains": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "pattern": r"^ssp:\/\/.+"}
                        },
                    },
                },
            },
        },
    },
}

NOT_SSP_DATA = {
    "author": [{"system": "XXX", "value": "XYZ"}],
    "content": [{"url": "http://foo.com"}, {"url": "http://foo.com"}],
}

HAS_SSP_DATA = {
    "author": [
        {"system": "https://fhir.nhs.uk/Id/accredited-system-id", "value": "123"},
        {"system": "XXX", "value": "XYZ"},
    ],
    "content": [{"url": "ssp://foo.com"}, {"url": "http://foo.com"}],
}


HAS_SSP_NO_AUTHOR_DATA = {
    "author": [{"system": "XXX", "value": "XYZ"}],
    "content": [{"url": "ssp://foo.com"}, {"url": "http://foo.com"}],
}

NOT_SSP_HAS_AUTHOR_DATA = {
    "author": [
        {"system": "https://fhir.nhs.uk/Id/accredited-system-id", "value": "123"},
        {"system": "XXX", "value": "XYZ"},
    ],
    "content": [{"url": "http://foo.com"}, {"url": "http://foo.com"}],
}

# The following is a example that involves nested and recursive referencing

RECORDING_JSON_SCHEMA = {
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


@pytest.mark.parametrize(
    ("instance", "error_message"),
    [
        (
            HAS_SSP_NO_AUTHOR_DATA,
            (
                "ValidationError raised from Data Contract 'None' at "
                "'content[0].url': "
                "'ssp://foo.com' does not match '^(?!ssp:\\\\/\\\\/).+'"
            ),
        ),
    ],
)
def test_validate_against_json_schema_ssp_examples_fail(instance, error_message):
    with pytest.raises(JsonSchemaValidationError) as exception_wrapper:
        validate_against_json_schema(
            json_schema=SSP_JSON_SCHEMA, contract_name=None, instance=instance
        )
    assert error_message == str(exception_wrapper.value)


@pytest.mark.parametrize(
    "instance",
    [HAS_SSP_DATA, NOT_SSP_HAS_AUTHOR_DATA, NOT_SSP_DATA],
)
def test_validate_against_json_schema_ssp_examples_pass(instance):
    validate_against_json_schema(
        json_schema=SSP_JSON_SCHEMA, contract_name=None, instance=instance
    )


@pytest.mark.parametrize("json_schema", [RECORDING_JSON_SCHEMA, SSP_JSON_SCHEMA])
def test_validate_json_schema(json_schema):
    validate_json_schema(json_schema=json_schema, contract_name=None)


@hypothesis.given(schema_for_a_recording=builds(SchemaForARecording))
def test_validate_against_json_schema_for_good_data(
    schema_for_a_recording: SchemaForARecording,
):
    instance = schema_for_a_recording.dict(exclude_none=True)
    validate_against_json_schema(
        json_schema=RECORDING_JSON_SCHEMA,
        contract_name="My Contract",
        instance=instance,
    )


@pytest.fixture
def repository():
    tf_json = get_terraform_json()
    account_id = tf_json["assume_account_id"]["value"]
    prefix = tf_json["prefix"]["value"] + "--"
    session = new_aws_session(account_id=account_id)
    client: DynamoDbClient = session.client("dynamodb")
    return Repository(item_type=Contract, client=client, environment_prefix=prefix)


@pytest.mark.integration
@pytest.mark.parametrize("random_seed", range(5))
@pytest.mark.parametrize(
    ["system", "value"],
    [
        ("", ""),  # Default case
        ("foo", "bar"),
    ],
)
def test__get_contracts_from_db_returns_latest_versions(
    random_seed: int, system: str, value: str, repository: Repository
):
    N_SCHEMA_TYPES = 3
    N_VERSIONS = 10
    MIN_VERSION = 1

    version_numbers: list[tuple[int, int]] = list(
        enumerate(reversed(range(MIN_VERSION, N_VERSIONS + MIN_VERSION)))
    )  # this is a list of <version, inverse_version>

    # to test that we're not just taking the latest version by construction
    # we shuffle the version numbers here so that we insert into dynamodb in a
    # non-linear way
    random.seed(random_seed)
    random.shuffle(version_numbers)
    random.seed(None)  # reset global seed

    for i_name in range(1, N_SCHEMA_TYPES + 1):
        for version, inverse_version in version_numbers:
            repository.create(
                item=Contract(
                    pk=key(DbPrefix.Contract, system, value),
                    sk=key(DbPrefix.Version, inverse_version, f"name{i_name}"),
                    name=f"name{i_name}",
                    version=str(version + 1),
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

    contracts = get_contracts_from_db(repository=repository, system=system, value=value)

    # There are {N_SCHEMA_TYPES} distinct contracts, each with {N_VERSIONS} versions
    # and the expectation is that only the latest versions are retrieved
    assert contracts == [
        Contract(
            pk=key(DbPrefix.Contract, system, value),
            sk=key(DbPrefix.Version, MIN_VERSION, "name1"),
            name="name1",
            version=str(N_VERSIONS),
            system=system,
            value=value,
            json_schema={
                "$schema": "http://json-schema.org/draft-04/schema#",
                "additionalProperties": False,
                "title": "Base 1",
                "type": "object",
            },
        ),
        Contract(
            pk=key(DbPrefix.Contract, system, value),
            sk=key(DbPrefix.Version, MIN_VERSION, "name2"),
            name="name2",
            version=str(N_VERSIONS),
            system=system,
            value=value,
            json_schema={
                "$schema": "http://json-schema.org/draft-04/schema#",
                "additionalProperties": False,
                "title": "Base 2",
                "type": "object",
            },
        ),
        Contract(
            pk=key(DbPrefix.Contract, system, value),
            sk=key(DbPrefix.Version, MIN_VERSION, "name3"),
            name=f"name3",
            version=str(N_VERSIONS),
            system=system,
            value=value,
            json_schema={
                "$schema": "http://json-schema.org/draft-04/schema#",
                "additionalProperties": False,
                "title": "Base 3",
                "type": "object",
            },
        ),
    ]

    # The validator is expecting a blank object only, so the following will pass
    for contract in contracts:
        validate_against_json_schema(
            json_schema=contract.json_schema.__root__,
            contract_name=contract.full_name,
            instance={},
        )

    # The validator is expecting a blank object only, so the following will fail
    for contract in contracts:
        with pytest.raises(JsonSchemaValidationError) as exception_wrapper:
            validate_against_json_schema(
                json_schema=contract.json_schema.__root__,
                contract_name=contract.full_name,
                instance={"foo": "bar"},
            )
        exception_wrapper.match(
            r"^ValidationError raised from Data Contract '\w+:\w+' at '\$': "
            r"Additional properties are not allowed \('foo' was unexpected\)$"
        )
