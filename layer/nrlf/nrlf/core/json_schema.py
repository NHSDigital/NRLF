from enum import Enum
from functools import wraps
from types import FunctionType
from typing import Type

from jsonschema import Draft7Validator as JSON_SCHEMA_VALIDATOR
from jsonschema import RefResolutionError, validate
from jsonschema.exceptions import FormatError, SchemaError, ValidationError
from jsonschema.exceptions import _Error as JsonSchemaBaseError
from lambda_utils.logging import log_action

from nrlf.core.constants import DbPrefix
from nrlf.core.errors import BadJsonSchema, JsonSchemaValidationError
from nrlf.core.model import Contract, key
from nrlf.core.repository import Repository


class LogReference(Enum):
    DATA_CONTRACT_READ_CACHE = "Getting cached Data Contracts"
    DATA_CONTRACT_WRITE_CACHE = "Caching Data Contracts"


DEFAULT_SYSTEM_VALUE = ""


class DataContractCache(dict):
    def get_global_contracts(self, logger=None) -> list[Contract]:
        return self.get(
            system=DEFAULT_SYSTEM_VALUE, value=DEFAULT_SYSTEM_VALUE, logger=logger
        )

    @log_action(
        log_reference=LogReference.DATA_CONTRACT_READ_CACHE,
        log_fields=["system", "value"],
    )
    def get(self, system: str, value: str) -> list[Contract]:
        return super().get(system, {}).get(value)

    def set_global_contracts(self, contracts: list[Contract], logger=None):
        return self.set(
            system=DEFAULT_SYSTEM_VALUE,
            value=DEFAULT_SYSTEM_VALUE,
            contracts=contracts,
            logger=logger,
        )

    @log_action(
        log_reference=LogReference.DATA_CONTRACT_WRITE_CACHE,
        log_fields=["system", "value", "contracts"],
    )
    def set(self, system: str, value: str, contracts: list[Contract]):
        return self.__setitem__(system, {value: contracts})


def _handle_json_schema_error(
    allowed_exception: Type[JsonSchemaBaseError],
    wrapper_exception: Type[Exception],
):
    def decorator(fn: FunctionType):
        @wraps(fn)
        def _validator(json_schema: dict, contract_name: str, **kwargs):
            try:
                fn(json_schema=json_schema, contract_name=contract_name, **kwargs)
            except allowed_exception as error:
                error = error.__dict__.get("_wrapped", error)
                error_message = error.__dict__.get("message", str(error))
                try:
                    error_path = error.json_path
                except AttributeError:
                    error_path = None
                message = _parse_json_schema_error(
                    error_class_name=error.__class__.__name__,
                    error_message=error_message,
                    error_path=error_path,
                    contract_name=contract_name,
                )
                raise wrapper_exception(message)

        return _validator

    return decorator


def _parse_json_schema_error(
    error_class_name: str, error_message: str, error_path: str, contract_name: str
) -> str:
    path = f" at '{error_path.replace('$.', '')}'" if error_path else ""
    return (
        f"{error_class_name} raised from Data Contract "
        f"'{contract_name}'{path}: {error_message}"
    )


@_handle_json_schema_error(
    allowed_exception=RefResolutionError,
    wrapper_exception=BadJsonSchema,
)
@_handle_json_schema_error(
    allowed_exception=SchemaError,
    wrapper_exception=BadJsonSchema,
)
def validate_json_schema(json_schema: dict, contract_name: str):
    """Note that 'contract_name' is soaked up in '_handle_json_schema_error'"""
    JSON_SCHEMA_VALIDATOR.check_schema(schema=json_schema)
    # The second step here is to check for unresolved references
    try:
        validate(schema=json_schema, instance={}, cls=JSON_SCHEMA_VALIDATOR)
    except ValidationError:  # We're not actually validating 'instance' here
        pass


@_handle_json_schema_error(
    allowed_exception=(ValidationError, FormatError),
    wrapper_exception=JsonSchemaValidationError,
)
def validate_against_json_schema(json_schema: dict, contract_name: str, instance: any):
    validate(schema=json_schema, instance=instance, cls=JSON_SCHEMA_VALIDATOR)


def get_contracts_from_db(
    repository: Repository,
    system: str = DEFAULT_SYSTEM_VALUE,
    value: str = DEFAULT_SYSTEM_VALUE,
    logger=None,
) -> list[Contract]:
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
    _contracts: list[Contract] = repository.query(pk=pk, logger=logger).items

    contracts: list[Contract] = []
    for contract in _contracts:
        # Retrieve the first contract for this name only, assuming that
        # they have been sorted in reverse order by Version
        if contract.name.__root__ in retrieved_contracts:
            continue
        retrieved_contracts.add(contract.name.__root__)
        # Validate the retrieved schema's syntax
        validate_json_schema(
            json_schema=contract.json_schema.__root__,
            contract_name=contract.full_name,
        )
        contracts.append(contract)

    return contracts
