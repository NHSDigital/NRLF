import json
from collections import ChainMap
from dataclasses import dataclass
from datetime import date
from itertools import chain
from pathlib import Path
from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits
from tempfile import TemporaryDirectory
from unittest import mock

import pytest
from hypothesis import given
from hypothesis.strategies import (
    builds,
    dates,
    dictionaries,
    from_regex,
    integers,
    just,
    lists,
    one_of,
    sampled_from,
    text,
)

from data_contracts.deploy_contracts.constants import (
    _PATH_TO_CONTRACTS_ROOT,
    PATH_PATTERNS,
    PATHS_TO_CONTRACTS,
    VERSION_SEPARATOR,
)
from data_contracts.deploy_contracts.deploy_contracts import (
    GroupedContracts,
    _active_contract_is_latest,
    _generate_calendar_version,
    _get_contracts_from_db,
    _get_contracts_to_deactivate,
    _get_contracts_to_deploy,
    _group_contracts,
    _increment_contract_sk,
    _increment_latest_version_on_conflict,
    _increment_patch_version,
    _increment_versions_of_contracts,
    _json_schema_from_file,
    _read_latest_json_schemas,
    _split_core_from_patch_version,
    sync_contracts,
)
from data_contracts.deploy_contracts.errors import (
    BadActiveContract,
    BadContractPath,
    BadVersionError,
)
from data_contracts.deploy_contracts.model import (
    ContractGroup,
    _strip_http_from_system,
    _substitute_http_from_system,
)
from feature_tests.common.repository import FeatureTestRepository as Repository
from feature_tests.common.utils import get_environment_prefix
from helpers.aws_session import new_aws_session
from nrlf.core.constants import DbPrefix
from nrlf.core.dynamodb_types import (
    DynamoDbStringType,
    convert_dynamo_value_to_raw_value,
)
from nrlf.core.json_schema import DEFAULT_SYSTEM_VALUE
from nrlf.core.model import Contract, DynamoDbModel, key

MOCK_PATH = "data_contracts.deploy_contracts.deploy_contracts.{}"
ASCII_TEXT = text(alphabet=ascii_letters + digits, min_size=1)
PK_REGEX = from_regex(r"C#(\w+)#(\w+)")
SK_REGEX = from_regex(r"V#(\d+)#(\w+)")


def mock_patch(target, *args, **kwargs):
    return mock.patch(MOCK_PATH.format(target), *args, **kwargs)


@given(today=one_of(dates(), just(None)))
def test__generate_calendar_version(today: date):
    if today is None:
        today = date.today()
    version = _generate_calendar_version(today=today)
    assert len(version) == 10

    year, month, day = map(int, version.split("."))
    assert today == date(year=year, month=month, day=day)


def test_contracts_exist():
    """
    A number of the following tests explicitly require that
    PATHS_TO_CONTRACTS is not empty - i.e. that there are
    valid JSON Schemas in this code repository. This test
    ensures that these exists, and the next test ensures
    that they are all valid.
    """
    assert len(PATHS_TO_CONTRACTS) > 0


@pytest.mark.parametrize("path", PATHS_TO_CONTRACTS)
def test_all_paths_to_contracts_yield_valid_contracts(path: str):
    """
    A number of the following tests explicitly require the
    JSON Schemas defined in PATHS_TO_CONTRACTS are valid,
    which this test ensures.
    """
    _json_schema_from_file(path=path)  # will raise an error on failure


@pytest.mark.parametrize("path", PATHS_TO_CONTRACTS)
def test__parse_contract_group_from_path(path: Path):
    group = ContractGroup.from_path(path=path)
    assert group.to_path(base_dir=_PATH_TO_CONTRACTS_ROOT) == path


@pytest.mark.parametrize(
    ("system_in", "system_out"),
    [
        ("http/snomed.info/sct", "http://snomed.info/sct"),
        ("https/snomed.info/sct", "https://snomed.info/sct"),
    ],
)
def test__substitute_http_from_path(system_in, system_out):
    assert _substitute_http_from_system(system=system_in) == system_out
    assert _strip_http_from_system(system=system_out) == system_in


@given(path=one_of(from_regex(regex, fullmatch=True) for regex in PATH_PATTERNS))
def test__parse_contract_group_from_path_good_path(path: str):
    while "//" in path:
        path = path.replace("//", "/")

    group: ContractGroup = ContractGroup.from_path(path=path)
    _path = group.to_path(base_dir="")
    _extra_base_dir = path.replace(str(_path), "")
    assert str(
        group.to_path(base_dir=_PATH_TO_CONTRACTS_ROOT / _extra_base_dir)
    ) == str(_PATH_TO_CONTRACTS_ROOT / path)


@pytest.mark.parametrize(
    "path",
    [
        (f"{_PATH_TO_CONTRACTS_ROOT}/http/snomed.info/sct/1213123/blah.json"),
        (f"{_PATH_TO_CONTRACTS_ROOT}/https/snomed.info/sct/1213123/blah.json"),
    ],
)
def test__parse_contract_group_from_path_url(path: str):
    group: ContractGroup = ContractGroup.from_path(path=path)
    _path = group.to_path(base_dir="")
    _extra_base_dir = path.replace(str(_path), "")
    assert str(
        group.to_path(base_dir=_PATH_TO_CONTRACTS_ROOT / _extra_base_dir)
    ) == str(_PATH_TO_CONTRACTS_ROOT / path)


@given(path=text())
def test__parse_contract_group_from_path_bad_path(path: str):
    with pytest.raises(BadContractPath):
        ContractGroup.from_path(path=path)


global_contract = builds(
    Contract,
    pk=PK_REGEX,
    sk=SK_REGEX,
    system=just(DEFAULT_SYSTEM_VALUE),
    value=just(DEFAULT_SYSTEM_VALUE),
    name=ASCII_TEXT,
    version=ASCII_TEXT,
)
local_contract = builds(
    Contract,
    pk=PK_REGEX,
    sk=SK_REGEX,
    system=ASCII_TEXT,
    value=ASCII_TEXT,
    name=ASCII_TEXT,
    version=ASCII_TEXT,
)
contract_strategy = one_of(global_contract, local_contract)


@given(contract=contract_strategy)
def test__parse_contract_group_from_contract(contract: Contract):
    group = ContractGroup.from_contract(contract=contract)
    assert group.system == contract.system.__root__
    assert group.value == contract.value.__root__
    assert group.name == contract.name.__root__


class DummyModel(DynamoDbModel):
    pk: DynamoDbStringType
    sk: DynamoDbStringType

    @classmethod
    def kebab(cls) -> str:
        return "document-pointer"


def _sort_contracts(contracts: list[Contract]) -> list[Contract]:
    return sorted(
        contracts,
        key=lambda contract: (contract.pk.__root__, contract.sk.__root__),
    )


@pytest.mark.integration  # Query by PK doesn't work in moto, so test has to be integration
def test__get_contracts_from_db():
    """
    Tests that only Contracts, not other objects e.g. 'Dummies' below
    are not retrieved from the database.
    """
    prefix = get_environment_prefix(test_mode=None)
    session = new_aws_session()
    client = session.client("dynamodb")
    contracts = [
        Contract(
            pk=f"C#{i}#{i}",
            sk=f"V#{j}#{j}",
            name="",
            version="",
            json_schema={},
            system="",
            value="",
        )
        for i in range(5)
        for j in range(2)
    ]

    dummies = [
        DummyModel(
            pk=f"FOO#{i}#{i}",
            sk=f"BAR#{j}#{j}",
        )
        for i in range(2)
        for j in range(3)
    ]

    repository = Repository(
        item_type=Contract, client=client, environment_prefix=prefix
    )
    repository.upsert_many(items=dummies + contracts)

    # Check that only contracts retrieved
    contracts_from_db = _get_contracts_from_db(repository=repository)
    assert _sort_contracts(contracts_from_db) == _sort_contracts(contracts)


@given(
    contract_groups=lists(
        builds(
            ContractGroup,
            system=sampled_from(("a", "b")),
            value=sampled_from(("x", "y")),
            name=sampled_from(("1", "2")),
        ),
    )
)
def test__group_contracts(contract_groups: list[ContractGroup]):
    """
    Tests that Contracts with the same system/value/name produce
    the same ContractGroup
    """
    unique_groups = set()
    contracts: list[Contract] = []
    for group in contract_groups:
        sk = key(DbPrefix.Version, 1, group.name)
        if group not in unique_groups:
            unique_groups.add(group)
            sk = group.active_sk
        contracts.append(
            Contract(
                pk=group.pk,
                sk=sk,
                json_schema={},
                version="",
                **group.dict(),
            )
        )

    contracts_by_group = _group_contracts(contracts=contracts)
    if contract_groups:
        assert len(contracts_by_group) > 0
    assert contracts_by_group.keys() == unique_groups

    unpacked_grouped_contracts = chain.from_iterable(contracts_by_group.values())
    assert _sort_contracts(unpacked_grouped_contracts) == _sort_contracts(contracts)


@given(group=builds(ContractGroup))
def test__group_contracts_bad_contracts(group: ContractGroup):
    """
    Tests that a list of Contracts can only be grouped
    if the first Contract is the active Contract (SK starts with V#0)
    """
    contracts = [
        Contract(
            pk=group.pk,
            sk=key(DbPrefix.Version, 1, group.name),
            json_schema={},
            version="",
            **group.dict(),
        )
    ]
    with pytest.raises(BadActiveContract):
        _group_contracts(contracts=contracts)


@mock_patch("ContractGroup")
@mock_patch("_json_schema_from_file")
@given(group_json_schema_pairs=dictionaries(keys=text(), values=text()))
def test__read_latest_json_schemas(
    mocked__json_schema_from_file,
    mocked_ContractGroup: ContractGroup,
    group_json_schema_pairs: dict[str, str],
):
    """
    Tests that local JSON Schemas are 'grouped' into a mapping of
    ContractGroup -> [JSON Schema], where each group is an array of size one
    """
    contract_groups_iter = iter(group_json_schema_pairs.keys())
    json_schemas_iter = iter(group_json_schema_pairs.values())

    mocked__json_schema_from_file.side_effect = lambda *args, **kwargs: next(
        json_schemas_iter
    )
    mocked_ContractGroup.from_path.side_effect = lambda *args, **kwargs: next(
        contract_groups_iter
    )
    n_schemas = len(group_json_schema_pairs)
    assert _read_latest_json_schemas(paths=range(n_schemas)) == {
        group: [json_schema] for group, json_schema in group_json_schema_pairs.items()
    }


@given(inverse_version=integers(), name=ASCII_TEXT, prefix=ASCII_TEXT)
def test__increment_contract_sk(inverse_version: int, name: str, prefix: str):
    sk_1 = DynamoDbStringType(__root__=f"{prefix}#{inverse_version}#{name}")
    sk_2 = DynamoDbStringType(__root__=f"{prefix}#{inverse_version+1}#{name}")
    assert _increment_contract_sk(sk=sk_1) == sk_2


def test__increment_patch_version_default():
    _next_patch_version = _increment_patch_version(patch_version=None)
    assert _next_patch_version == "a"


@pytest.mark.parametrize(
    ["patch_version", "next_patch_version"],
    zip(ascii_lowercase[:-1], ascii_lowercase[1:]),
)
def test__increment_patch_version_up_to_z(patch_version: str, next_patch_version: str):
    _next_patch_version = _increment_patch_version(patch_version=patch_version)
    assert _next_patch_version != patch_version
    assert _next_patch_version == next_patch_version


@pytest.mark.parametrize(
    "patch_version", ["z", *map(str.upper, ascii_uppercase), *digits]
)
def test__increment_patch_version_fails_after_z(patch_version: str):
    with pytest.raises(BadVersionError):
        _increment_patch_version(patch_version=patch_version)


def test__split_core_from_patch_version_3_parts():
    version = VERSION_SEPARATOR.join(map(str, range(3)))
    core_version, patch_version = _split_core_from_patch_version(version=version)
    assert core_version == "0.1.2"
    assert patch_version is None


def test__split_core_from_patch_version_4_parts():
    version = VERSION_SEPARATOR.join(map(str, range(4)))
    core_version, patch_version = _split_core_from_patch_version(version=version)
    assert core_version == "0.1.2"
    assert patch_version == "3"


@pytest.mark.parametrize("n_parts", (*range(2), *range(5, 10)))
def test__split_core_from_patch_version_not_3_or_4_parts(n_parts):
    version = VERSION_SEPARATOR.join(map(str, range(n_parts)))
    with pytest.raises(BadVersionError):
        _split_core_from_patch_version(version=version)


@given(contract=builds(Contract, version=just("1.2.3.a")))
def test__increment_version_on_conflict(contract: Contract):
    _increment_latest_version_on_conflict(
        contracts=[contract], latest_version="1.2.3.a"
    ) == "1.2.3.b"


@given(contract=builds(Contract, version=just("1.2.3.a")))
def test__increment_version_on_conflict_no_conflict(contract: Contract):
    _increment_latest_version_on_conflict(
        contracts=[contract], latest_version="1.2.3.0"
    ) == "1.2.3.a"


@given(
    contracts=lists(
        builds(Contract, sk=from_regex(r"V#{\d+}#{\w+}")),
        unique_by=lambda contract: contract.sk.__root__,
    )
)
@mock_patch("_increment_contract_sk")
def test__increment_versions_of_contracts(
    mocked__increment_contract_sk, contracts: list[Contract]
):
    mocked__increment_contract_sk.side_effect = lambda sk: DynamoDbStringType(
        __root__=sk.__root__ + "foo"
    )

    expected_contracts = []
    for contract in contracts:
        raw_contract = {
            k: convert_dynamo_value_to_raw_value(v) for k, v in contract.dict().items()
        }

        raw_contract["sk"] = raw_contract["sk"] + "foo"
        expected_contracts.append(Contract(**raw_contract))

    assert _increment_versions_of_contracts(contracts=contracts) == expected_contracts


@given(
    contracts=lists(builds(Contract), min_size=1),
    json_schema=dictionaries(keys=integers(), values=integers(), min_size=1),
)
def test__active_contract_is_latest(contracts: list[Contract], json_schema: dict):
    contracts[0].json_schema.__root__ = json_schema
    assert _active_contract_is_latest(contracts=contracts, json_schema=json_schema)


@given(
    json_schema=dictionaries(keys=integers(), values=integers(), min_size=1),
)
def test__active_contract_is_not_latest_when_empty(json_schema: dict):
    assert not _active_contract_is_latest(contracts=[], json_schema=json_schema)


@given(
    contracts=lists(builds(Contract), min_size=1),
    active_json_schema=dictionaries(keys=text(), values=text(), min_size=1),
    json_schema=dictionaries(keys=integers(), values=integers(), min_size=1),
)
def test__active_contract_is_not_latest_when_json_schema_different(
    contracts: list[Contract], active_json_schema: dict, json_schema: dict
):
    contracts[0].json_schema.__root__ = active_json_schema
    assert not _active_contract_is_latest(contracts=contracts, json_schema=json_schema)


def test__get_contracts_to_deactivate():
    """
    Test that contracts in grouped_db_contracts will be deactivated
    if they don't exist in latest_groups
    """
    grouped_db_contracts = {
        ContractGroup(system="snomed", value="123", name="foo"): [
            Contract(
                pk="C#snomed#123",
                sk="V#0#foo",
                system="snomed",
                value="123",
                name="foo",
                version="0.0.0.3",
                json_schema={"foo": "FOO3"},
            ),
            Contract(
                pk="C#snomed#123",
                sk="V#1#foo",
                system="snomed",
                value="123",
                name="foo",
                version="0.0.0.2",
                json_schema={"foo": "FOO2"},
            ),
            Contract(
                pk="C#snomed#123",
                sk="V#2#foo",
                system="snomed",
                value="123",
                name="foo",
                version="0.0.0.1",
                json_schema={"foo": "FOO1"},
            ),
        ],
        ContractGroup(system="snomed", value="123", name="bar"): [
            Contract(
                pk="C#snomed#123",
                sk="V#0#bar",
                system="snomed",
                value="123",
                name="bar",
                version="0.0.0.2",
                json_schema={"bar": "BAR2"},
            ),
            Contract(
                pk="C#snomed#123",
                sk="V#1#bar",
                system="snomed",
                value="123",
                name="bar",
                version="0.0.0.1",
                json_schema={"bar": "BAR1"},
            ),
        ],
    }

    latest_groups = [ContractGroup(system="snomed", value="123", name="bar")]
    latest_version = "1.2.3.4"

    contracts_to_deactivate = list(
        _get_contracts_to_deactivate(
            grouped_db_contracts=grouped_db_contracts,
            latest_groups=latest_groups,
            latest_version=latest_version,
        )
    )

    assert contracts_to_deactivate == [
        Contract(
            pk="C#snomed#123",
            sk="V#0#foo",
            system="snomed",
            value="123",
            name="foo",
            version=latest_version,
            json_schema={},
        ),
        Contract(
            pk="C#snomed#123",
            sk="V#1#foo",
            system="snomed",
            value="123",
            name="foo",
            version="0.0.0.3",
            json_schema={"foo": "FOO3"},
        ),
        Contract(
            pk="C#snomed#123",
            sk="V#2#foo",
            system="snomed",
            value="123",
            name="foo",
            version="0.0.0.2",
            json_schema={"foo": "FOO2"},
        ),
        Contract(
            pk="C#snomed#123",
            sk="V#3#foo",
            system="snomed",
            value="123",
            name="foo",
            version="0.0.0.1",
            json_schema={"foo": "FOO1"},
        ),
    ]


def test__get_contracts_to_deploy():
    """
    Test that contracts not in grouped_db_contracts will be deployed
    if they don't exist OR are out of step with those in latest_groups
    """
    grouped_db_contracts = {
        ContractGroup(system="snomed", value="123", name="foo"): [
            Contract(
                pk="C#snomed#123",
                sk="V#0#foo",
                system="snomed",
                value="123",
                name="foo",
                version="0.0.0.3",
                json_schema={"foo": "FOO3"},
            ),
            Contract(
                pk="C#snomed#123",
                sk="V#1#foo",
                system="snomed",
                value="123",
                name="foo",
                version="0.0.0.2",
                json_schema={"foo": "FOO2"},
            ),
            Contract(
                pk="C#snomed#123",
                sk="V#2#foo",
                system="snomed",
                value="123",
                name="foo",
                version="0.0.0.1",
                json_schema={"foo": "FOO1"},
            ),
        ],
        ContractGroup(system="snomed", value="123", name="bar"): [
            Contract(
                pk="C#snomed#123",
                sk="V#0#bar",
                system="snomed",
                value="123",
                name="bar",
                version="0.0.0.2",
                json_schema={"bar": "BAR2"},
            ),
            Contract(
                pk="C#snomed#123",
                sk="V#1#bar",
                system="snomed",
                value="123",
                name="bar",
                version="0.0.0.1",
                json_schema={"bar": "BAR1"},
            ),
        ],
    }

    grouped_latest_json_schemas = {
        ContractGroup(system="snomed", value="123", name="bar"): [{"bar": "BAR_X"}],
        ContractGroup(system="snomed", value="123", name="foo"): [{"foo": "FOO_X"}],
    }

    latest_version = "1.2.3.4"

    contracts_to_deploy = list(
        _get_contracts_to_deploy(
            grouped_db_contracts=grouped_db_contracts,
            grouped_latest_json_schemas=grouped_latest_json_schemas,
            latest_version=latest_version,
        )
    )

    assert contracts_to_deploy == [
        Contract(
            pk="C#snomed#123",
            sk="V#0#bar",
            system="snomed",
            value="123",
            name="bar",
            version=latest_version,
            json_schema={"bar": "BAR_X"},
        ),
        Contract(
            pk="C#snomed#123",
            sk="V#1#bar",
            system="snomed",
            value="123",
            name="bar",
            version="0.0.0.2",
            json_schema={"bar": "BAR2"},
        ),
        Contract(
            pk="C#snomed#123",
            sk="V#2#bar",
            system="snomed",
            value="123",
            name="bar",
            version="0.0.0.1",
            json_schema={"bar": "BAR1"},
        ),
        Contract(
            pk="C#snomed#123",
            sk="V#0#foo",
            system="snomed",
            value="123",
            name="foo",
            version=latest_version,
            json_schema={"foo": "FOO_X"},
        ),
        Contract(
            pk="C#snomed#123",
            sk="V#1#foo",
            system="snomed",
            value="123",
            name="foo",
            version="0.0.0.3",
            json_schema={"foo": "FOO3"},
        ),
        Contract(
            pk="C#snomed#123",
            sk="V#2#foo",
            system="snomed",
            value="123",
            name="foo",
            version="0.0.0.2",
            json_schema={"foo": "FOO2"},
        ),
        Contract(
            pk="C#snomed#123",
            sk="V#3#foo",
            system="snomed",
            value="123",
            name="foo",
            version="0.0.0.1",
            json_schema={"foo": "FOO1"},
        ),
    ]


@mock_patch("_generate_calendar_version")
@mock_patch("_read_latest_json_schemas")
@mock_patch("_get_contracts_from_db")
@mock_patch("_group_contracts")
@mock_patch("_get_contracts_to_deactivate", return_value=range(3))
@mock_patch("_get_contracts_to_deploy", return_value=range(4))
def test_sync_contracts(
    _mock_generate, _mock_read, _mock_get, _mock_group, _mock_deactivate, _mock_deploy
):
    """
    Test that 'sync_contracts' will concatenate the outputs of
    _get_contracts_to_deactivate and _get_contracts_to_deploy
    and pass them to repository.upsert_many
    """
    repository = mock.Mock(spec=Repository)

    @dataclass
    class Container:
        items: list[int]

        def upsert_many(self, items):
            self.items = items

    container = Container(items=None)
    repository.upsert_many.side_effect = container.upsert_many

    sync_contracts(repository=repository)

    # i.e. the items from the above ranges
    assert container.items == [0, 1, 2, 0, 1, 2, 3]


def _create_contract_group(
    suffix: str,
    n_contracts: int,
    json_schema: dict,
    local_base_dir: Path = None,
    local_json_schema: dict = None,
) -> GroupedContracts:
    """
    Create a mapping of ContractGroup to Contracts in the database,
    optionally creating a local json schema for that contract group
    """
    group = ContractGroup(
        name=f"name_{suffix}", system=f"system_{suffix}", value=f"value_{suffix}"
    )

    if local_base_dir and local_json_schema:
        path_to_json_schema_file = group.to_path(base_dir=local_base_dir)
        path_to_json_schema_file.parent.mkdir(parents=True)
        with open(file=path_to_json_schema_file, mode="w") as f:
            f.write(json.dumps(local_json_schema))

    return {
        group: _sort_contracts(
            Contract(
                pk=f"C#{group.system}#{group.value}",
                sk=f"V#{n_contracts-(i+1)}#{group.name}",
                version=f"1900.01.{str(i).zfill(2)}",
                json_schema=json_schema,
                **group.dict(),
            )
            for i in range(n_contracts)
        )
    }


@pytest.fixture(scope="function")
def temp_dir() -> Path:
    """
    Create a temp directory for mocking data contracts,
    with the root contract dir '_PATH_TO_CONTRACTS_ROOT' mocked
    at the base of the temp directory
    """
    root_path_parts = filter(lambda x: x != "/", _PATH_TO_CONTRACTS_ROOT.parts)
    with TemporaryDirectory() as dir:
        absolute_dir = Path(dir).resolve()
        _path = absolute_dir.joinpath(*root_path_parts)
        assert str(_path).startswith(str(absolute_dir))

        _path.mkdir(parents=True)
        yield _path


@pytest.mark.integration
def test_sync_contracts_e2e(temp_dir):
    """
    Tests the behaviour of synchronising a initial state is entirely
    deterministic. Read the comments for a walkthrough.
    """
    session = new_aws_session()
    client = session.client("dynamodb")
    environment_prefix = get_environment_prefix(None)
    repository = Repository(
        item_type=Contract, client=client, environment_prefix=environment_prefix
    )

    EMPTY_SCHEMA = {}
    OLD_SCHEMA = {"name": "old schema"}
    NEW_SCHEMA = {"name": "new schema"}

    # Create a contract group without a local counterpart - to be deactivated by the sync
    contracts_to_be_deactivated = _create_contract_group(
        suffix="to_deactivate",
        n_contracts=3,
        json_schema=OLD_SCHEMA,
    )

    # Create a contract group without a local counterpart - which are already deactivated so to be skipped by the sync
    contracts_already_deactivated = _create_contract_group(
        suffix="already_deactivated",
        n_contracts=2,
        json_schema=EMPTY_SCHEMA,
    )

    # Create a contract group with a local counterpart - to be superseded by the sync
    contracts_to_be_superseded = _create_contract_group(
        suffix="to_supersede",
        n_contracts=5,
        json_schema=OLD_SCHEMA,
        local_base_dir=temp_dir,
        local_json_schema=NEW_SCHEMA,
    )

    # Create a contract group with a local counterpart - to be superseded by the sync
    contracts_to_be_skipped = _create_contract_group(
        suffix="to_skip",
        n_contracts=3,
        json_schema=OLD_SCHEMA,
        local_base_dir=temp_dir,
        local_json_schema=OLD_SCHEMA,
    )

    # Create a contract group without a db counterpart - to be created by the sync
    contracts_to_be_created = _create_contract_group(
        suffix="to_create",
        n_contracts=0,
        json_schema=None,
        local_base_dir=temp_dir,
        local_json_schema=NEW_SCHEMA,
    )

    initial_input_contracts = list(
        chain.from_iterable(
            ChainMap(
                contracts_to_be_deactivated,
                contracts_already_deactivated,
                contracts_to_be_superseded,
                contracts_to_be_skipped,
            ).values()
        )
    )

    repository.upsert_many(
        items=initial_input_contracts
    )  # Create items that should already exist

    # Verify the initial state
    initial_db_contracts = _get_contracts_from_db(repository=repository)
    assert _sort_contracts(initial_input_contracts) == _sort_contracts(
        initial_db_contracts
    )

    # Deploy the contracts
    today = date(year=2000, month=1, day=1)
    paths = list(Path(temp_dir).glob("**/*json"))
    result = sync_contracts(
        repository=repository, today=today, paths_to_json_schemas=paths
    )
    assert result is True

    # Verify the state
    synced_db_contracts = _get_contracts_from_db(repository=repository)
    assert initial_db_contracts != synced_db_contracts  # i.e. an update has taken place
    assert (
        len(synced_db_contracts) == len(initial_db_contracts) + 3
    )  # to_be_deactivated, to_be_superseded, to_be_created

    # Get the groups that haven't changed
    grouped_initial_contracts = _group_contracts(contracts=initial_db_contracts)
    grouped_synced_contracts = _group_contracts(contracts=synced_db_contracts)

    grouped_unchanged_contracts: GroupedContracts = {}
    grouped_changed_contracts: GroupedContracts = {}
    for group, _contracts in grouped_synced_contracts.items():
        if _contracts == grouped_initial_contracts[group]:
            grouped_unchanged_contracts[group] = _sort_contracts(_contracts)
        else:
            grouped_changed_contracts[group] = _sort_contracts(_contracts)

    expected_grouped_unchanged_contracts = ChainMap(
        contracts_already_deactivated,
        contracts_to_be_skipped,
    )
    assert grouped_unchanged_contracts == expected_grouped_unchanged_contracts

    assert grouped_changed_contracts[
        ContractGroup(
            name="name_to_deactivate",
            system="system_to_deactivate",
            value="value_to_deactivate",
        )
    ][0] == Contract(
        pk=f"C#system_to_deactivate#value_to_deactivate",
        sk=f"V#0#name_to_deactivate",
        name="name_to_deactivate",
        system="system_to_deactivate",
        value="value_to_deactivate",
        version="2000.01.01",
        json_schema=EMPTY_SCHEMA,
    )

    assert grouped_changed_contracts[
        ContractGroup(
            name="name_to_supersede",
            system="system_to_supersede",
            value="value_to_supersede",
        )
    ][0] == Contract(
        pk=f"C#system_to_supersede#value_to_supersede",
        sk=f"V#0#name_to_supersede",
        name="name_to_supersede",
        system="system_to_supersede",
        value="value_to_supersede",
        version="2000.01.01",
        json_schema=NEW_SCHEMA,
    )

    assert grouped_changed_contracts[
        ContractGroup(
            name="name_to_create",
            system="system_to_create",
            value="value_to_create",
        )
    ][0] == Contract(
        pk=f"C#system_to_create#value_to_create",
        sk=f"V#0#name_to_create",
        name="name_to_create",
        system="system_to_create",
        value="value_to_create",
        version="2000.01.01",
        json_schema=NEW_SCHEMA,
    )

    # Verify nothing done after initial
    result = sync_contracts(
        repository=repository, today=today, paths_to_json_schemas=paths
    )
    assert result is False

    repository.delete_all()


@pytest.mark.integration
def test_sync_actual_contracts_e2e():
    """Test that all of the contracts are synced even when they are symlinks"""
    session = new_aws_session()
    client = session.client("dynamodb")
    environment_prefix = get_environment_prefix(None)
    repository = Repository(
        item_type=Contract, client=client, environment_prefix=environment_prefix
    )

    # Verify the initial state
    initial_db_contracts = _get_contracts_from_db(repository=repository)
    assert initial_db_contracts == []

    # Deploy the contracts
    today = date(year=2000, month=1, day=1)
    result = sync_contracts(repository=repository, today=today)
    assert result is True

    # Verify the contracts have been deployed
    synced_db_contracts = _get_contracts_from_db(repository=repository)
    assert initial_db_contracts != synced_db_contracts  # i.e. an update has taken place
    assert len(synced_db_contracts) == len(PATHS_TO_CONTRACTS)

    repository.delete_all()
