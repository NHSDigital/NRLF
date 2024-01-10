from collections import defaultdict
from datetime import date
from itertools import chain
from pathlib import Path
from string import ascii_lowercase
from typing import Generator

from fire import Fire

from helpers.aws_session import new_session_from_env
from nrlf.core.constants import KEY_SEPARATOR
from nrlf.core.dynamodb_types import DynamoDbStringType
from nrlf.core.json_schema import validate_json_schema
from nrlf.core.model import Contract, key
from nrlf.core.repository import Repository
from nrlf.core.validators import json_load

from .constants import (
    CONTRACT_PK_WILDCARD,
    EMPTY_SCHEMA,
    PATHS_TO_CONTRACTS,
    VERSION_SEPARATOR,
)
from .errors import BadActiveContract, BadVersionError, DeploymentExceptions
from .model import ContractGroup

GroupedContracts = dict[ContractGroup, list[Contract]]
GroupedJsonSchemas = dict[ContractGroup, list[dict]]


def _generate_calendar_version(today: date = None) -> str:
    if today is None:
        today = date.today()
    return VERSION_SEPARATOR.join(
        (f"{today.year:04d}", f"{today.month:02d}", f"{today.day:02d}")
    )


def _json_schema_from_file(path: str) -> dict:
    with open(path) as f:
        json_schema = json_load(f)
    validate_json_schema(json_schema=json_schema, contract_name=path)
    return json_schema


def _get_contracts_from_db(repository: Repository[Contract]) -> list[Contract]:
    return repository.query_gsi_1(pk=CONTRACT_PK_WILDCARD, limit=-1).items


def _group_contracts(contracts: list[Contract]) -> GroupedContracts:
    """
    Maps the ContractGroup onto the Contracts from the database,
    which enables easy comparison with GroupedJsonSchemas from the
    local paths.
    """
    contracts_by_group: GroupedContracts = defaultdict(list[Contract])
    for contract in contracts:
        group = ContractGroup.from_contract(contract=contract)
        contracts_by_group[group].append(contract)

    for contract_group, _contracts in contracts_by_group.items():
        # Active Contract should always be first
        active_contract_sk = _contracts[0].sk.__root__
        if active_contract_sk != contract_group.active_sk:
            raise BadActiveContract(
                f"The sort key of the active Contract '{contract_group.dict()}' "
                "does not match the expected sort key of active Contracts for "
                f"this group. Expected sort key: '{contract_group.active_sk}', "
                f"got: '{active_contract_sk}'"
            )

    return contracts_by_group


def _read_latest_json_schemas(paths: list[Path]) -> GroupedJsonSchemas:
    """
    Maps the ContractGroup onto the Json Schema for each path,
    which enables easy comparison with GroupedContracts from the
    database.
    """
    contracts_by_group: GroupedJsonSchemas = defaultdict(list)
    for path in paths:
        group = ContractGroup.from_path(path=path)
        json_schema = _json_schema_from_file(path=path)
        contracts_by_group[group].append(json_schema)
    return contracts_by_group


def _increment_contract_sk(sk: DynamoDbStringType) -> DynamoDbStringType:
    prefix, inverse_version, name = sk.__root__.split(KEY_SEPARATOR)
    incremented_inverse_version = f"{int(inverse_version) + 1}"
    return DynamoDbStringType(__root__=key(prefix, incremented_inverse_version, name))


def _split_core_from_patch_version(version: str):
    parts = version.split(VERSION_SEPARATOR)
    n_parts = len(parts)
    if n_parts in (3, 4):
        core_version = VERSION_SEPARATOR.join(parts[:3])
        patch_version = None
        if n_parts == 4:
            patch_version = parts[-1]
        return core_version, patch_version
    raise BadVersionError(
        f"Version expected to be in 3 or 4 parts, got '{version}' ({n_parts} parts)"
    )


def _increment_patch_version(patch_version: str):
    if patch_version is None:
        return ascii_lowercase[0]
    if patch_version not in list(ascii_lowercase[:-1]):
        raise BadVersionError(
            f"Cannot increment patch version '{patch_version}', it must be one of {ascii_lowercase[:-1]}"
        )
    char_index = ascii_lowercase.index(patch_version)
    return ascii_lowercase[char_index + 1]


def _increment_latest_version_on_conflict(
    contracts: list[Contract], latest_version: str
) -> str:
    active_contract = contracts[0] if contracts else None
    core_latest_version, _ = _split_core_from_patch_version(version=latest_version)
    if active_contract:
        core_active_version, patch_active_version = _split_core_from_patch_version(
            version=active_contract.version.__root__
        )
        if core_active_version == core_latest_version:
            next_patch_version = _increment_patch_version(
                patch_version=patch_active_version
            )
            return VERSION_SEPARATOR.join((core_latest_version, next_patch_version))
    return latest_version


def _increment_versions_of_contracts(contracts: list[Contract]) -> list[Contract]:
    return [
        contract.copy(update={"sk": _increment_contract_sk(sk=contract.sk)})
        for contract in contracts
    ]


def _active_contract_is_latest(contracts: list[Contract], json_schema: dict):
    active_contract = contracts[0] if contracts else None
    return active_contract and (active_contract.json_schema.__root__ == json_schema)


def _get_contracts_to_deactivate(
    grouped_db_contracts: GroupedContracts,
    latest_groups: list[ContractGroup],
    latest_version: str,
) -> Generator[Contract, None, None]:
    """
    If any ContractGroup from the database is no longer present on disk,
    then 'deactivate' the ContractGroup by creating a latest version
    of the Contract with an empty JSON Schema.
    """
    for contract_group, contracts in grouped_db_contracts.items():
        if contract_group in latest_groups:
            continue
        if _active_contract_is_latest(contracts=contracts, json_schema=EMPTY_SCHEMA):
            # i.e. this ContractGroup has already been 'deactivated'
            continue
        _latest_version = _increment_latest_version_on_conflict(
            contracts=contracts, latest_version=latest_version
        )
        yield contract_group.to_active_contract(
            json_schema=EMPTY_SCHEMA, version=_latest_version
        )
        yield from _increment_versions_of_contracts(contracts=contracts)


def _get_contracts_to_deploy(
    grouped_db_contracts: GroupedContracts,
    grouped_latest_json_schemas: GroupedJsonSchemas,
    latest_version: str,
) -> Generator[Contract, None, None]:
    for contract_group, (json_schema,) in grouped_latest_json_schemas.items():
        contracts = grouped_db_contracts.get(contract_group, [])
        if _active_contract_is_latest(contracts=contracts, json_schema=json_schema):
            continue
        _latest_version = _increment_latest_version_on_conflict(
            contracts=contracts, latest_version=latest_version
        )
        yield contract_group.to_active_contract(
            json_schema=json_schema, version=_latest_version
        )
        yield from _increment_versions_of_contracts(contracts=contracts)


def sync_contracts(
    repository: Repository[Contract],
    paths_to_json_schemas: str = PATHS_TO_CONTRACTS,
    today: date = None,
) -> bool:
    calendar_version = _generate_calendar_version(today=today)
    grouped_latest_json_schemas = _read_latest_json_schemas(paths=paths_to_json_schemas)

    db_contracts = _get_contracts_from_db(repository=repository)
    grouped_db_contracts = _group_contracts(contracts=db_contracts)

    contracts_to_deactivate = _get_contracts_to_deactivate(
        grouped_db_contracts=grouped_db_contracts,
        latest_groups=grouped_latest_json_schemas.keys(),
        latest_version=calendar_version,
    )
    contracts_to_deploy = _get_contracts_to_deploy(
        grouped_db_contracts=grouped_db_contracts,
        grouped_latest_json_schemas=grouped_latest_json_schemas,
        latest_version=calendar_version,
    )

    contracts_to_put = list(chain(contracts_to_deactivate, contracts_to_deploy))
    if contracts_to_put:
        repository.upsert_many(items=contracts_to_put)
    return bool(contracts_to_put)


class NothingToDo(Exception):
    pass


def sync(environment: str, workspace: str):
    environment_prefix = f"nhsd-nrlf--{workspace}--"

    session = new_session_from_env(env=environment)
    client = session.client("dynamodb")
    repository = Repository(
        item_type=Contract, client=client, environment_prefix=environment_prefix
    )

    if not sync_contracts(repository=repository):
        raise NothingToDo


if __name__ == "__main__":
    try:
        Fire(sync)
    except DeploymentExceptions as err:
        print(  # noqa: T201
            "🚨 An Error Occurred 🚨", f"{err.__class__.__name__}: {err}", sep="\n"
        )
    except NothingToDo:
        print("😐 Already synchronised: nothing to do 😐")  # noqa: T201
    else:
        print("✅ Data Contracts synchronised successfully ✅")  # noqa: T201
