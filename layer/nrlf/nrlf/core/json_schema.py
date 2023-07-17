import importlib.util
import json
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import FunctionType, ModuleType
from typing import Generator

from datamodel_code_generator.parser.jsonschema import JsonSchemaParser
from pydantic import BaseModel

from nrlf.core.constants import DbPrefix
from nrlf.core.errors import BadJsonSchema
from nrlf.core.model import Contract, key
from nrlf.core.repository import Repository

NON_ALPHANUMERIC = re.compile(r"[^a-zA-Z0-9]+")
UPPER_CAMEL_CASE = re.compile(r"[A-Z][a-zA-Z0-9]+")
LOWER_CAMEL_CASE = re.compile(r"[a-z][a-zA-Z0-9]+")


class JsonSchemaValidatorCache(dict):
    """A cache for validators generated from JSON Schema"""

    def get_global_validators(self) -> list[FunctionType]:
        return self.get(system="", value="")

    def get(self, system: str, value: str) -> list[FunctionType]:
        return super().get(system, {}).get(value)

    def set_global_validators(self, validators: list[FunctionType]):
        return self.set(system="", value="", validators=validators)

    def set(self, system: str, value: str, validators: list[FunctionType]):
        return self.__setitem__(system, {value: validators})


def _to_camel_case(name: str) -> str:
    if any(NON_ALPHANUMERIC.finditer(name)):
        return "".join(term.lower().title() for term in NON_ALPHANUMERIC.split(name))
    if UPPER_CAMEL_CASE.match(name):
        return name
    if LOWER_CAMEL_CASE.match(name):
        return name[0].upper() + name[1:]
    raise BadJsonSchema(f"Unknown case used for {name}")


def _load_module_from_file(file_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        name=file_path.stem, location=str(file_path)
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[file_path.stem] = module
    spec.loader.exec_module(module)
    return module


@contextmanager
def _delete_file_on_completion(file_path: Path):
    try:
        yield
    finally:
        file_path.unlink(missing_ok=True)


def json_schema_to_pydantic_model(json_schema: dict, name_override: str) -> BaseModel:
    json_schema_as_str = json.dumps(json_schema)
    pydantic_models_as_str: str = JsonSchemaParser(json_schema_as_str).parse()

    with NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file_path = Path(temp_file.name).resolve()
        temp_file.write(pydantic_models_as_str.encode())

    with _delete_file_on_completion(file_path=temp_file_path):
        module = _load_module_from_file(file_path=temp_file_path)

    main_model_name = _to_camel_case(name=json_schema["title"])
    pydantic_model = module.__dict__[main_model_name]
    # Override the pydantic model name for nicer ValidationError messaging
    pydantic_model.__name__ = name_override
    return pydantic_model


def _get_contracts_from_db(
    repository: Repository, system: str, value: str
) -> Generator[Contract, None, None]:
    """
    When a querying DynamoDb by PK (i.e. SK is omitted) then all items
    with that PK are returned, sorted by the SK. In the case of the Data Contracts,
    the SK is "V#<inverse_version>#<contract_name>". This function therefore
    returns all distinct Data Contracts (defined by <contract_name>)
    for the given system|value, for the latest version (lowest inverse_version)
    of each distinct Data Contract.
    """
    retrieved_contracts = set()
    pk = key(DbPrefix.Contract, system, value)
    contracts: list[Contract] = repository.query(pk=pk).items
    for contract in contracts:
        # Retrieve the first validator for this name only, assuming that
        # they have been sorted in reverse order by Version
        if contract.name.__root__ in retrieved_contracts:
            continue
        retrieved_contracts.add(contract.name.__root__)
        yield contract


def get_validators_from_db(
    repository: Repository, system: str = "", value: str = ""
) -> list[FunctionType]:
    validators = []
    for contract in _get_contracts_from_db(
        repository=repository, system=system, value=value
    ):
        pydantic_model = json_schema_to_pydantic_model(
            json_schema=contract.json_schema.__root__,
            # Override the pydantic model name for nicer ValidationError messaging
            name_override=f"Data Contract '{contract.name.__root__}'",
        )
        validators.append(pydantic_model.parse_obj)
    return validators
