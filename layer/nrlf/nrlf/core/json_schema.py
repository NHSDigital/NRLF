import importlib.util
import json
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import FunctionType

from datamodel_code_generator import InputFileType, generate
from pydantic import BaseModel

from nrlf.core.constants import DbPrefix
from nrlf.core.model import Contract, key
from nrlf.core.repository import Repository


class JsonSchemaMapping(dict):
    def get_default(self) -> list[FunctionType]:
        return self.get(system="", value="")

    def get(system: str, value: str) -> list[FunctionType]:
        return super().get(system, {}).get(value)

    def set_default(self, validators: list[FunctionType]):
        return self.set(system="", value="", validators=validators)

    def set(self, system: str, value: str, validators: list[FunctionType]):
        return self.__setitem__(system, {value: validators})


def json_schema_to_pydantic_model(json_schema: dict) -> BaseModel:
    with NamedTemporaryFile(suffix=".py") as temp_file:
        temp_file_path = Path(temp_file.name)
        generate(
            json.dumps(json_schema),
            output=temp_file_path,
            input_file_type=InputFileType.JsonSchema,
        )
        spec = importlib.util.spec_from_file_location(
            name=temp_file_path.stem, location=str(temp_file_path)
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[temp_file.name] = module
        spec.loader.exec_module(module)
    return module.__dict__[json_schema["title"]]


def get_validators_from_db(
    repository: Repository, system: str = "", value: str = ""
) -> list[FunctionType]:
    validators = dict[str, FunctionType]
    for page in repository.query(pk=key(DbPrefix.Contract, system, value)):
        contracts: list[Contract] = page.items
        for contract in contracts:
            pydantic_model = json_schema_to_pydantic_model(
                json_schema=contract.schema.__root__
            )
            pydantic_model.__name__ = contract.name.__root__  # label the error message
            # Retrieve the first validator for this name only, assuming that
            # they have been sorted in reverse order by Version
            if contract.name.__root__ in validators:
                continue
            validators[contract.name.__root__] = pydantic_model.parse_obj
    return list(validators.values())
