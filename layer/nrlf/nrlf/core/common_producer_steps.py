from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import add_log_fields, log_action

from nrlf.core.constants import CUSTODIAN_SEPARATOR
from nrlf.core.errors import RequestValidationError
from nrlf.core.json_schema import (
    DataContractCache,
    get_contracts_from_db,
    validate_against_json_schema,
)
from nrlf.core.model import (
    APIGatewayProxyEventModel,
    DocumentPointer,
    split_pointer_type,
)
from nrlf.core.repository import Repository
from nrlf.core.validators import generate_producer_id
from nrlf.log_references import LogReference


@log_action(log_reference=LogReference.COMMON_PRODUCER_VALIDATE_PERMISSIONS)
def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    # Compare producer id from path id to ods code from NHSD-Connection-Metadata
    producer_id = data["producer_id"]
    ods_code_parts = data["ods_code_parts"]
    add_log_fields(producer_id=producer_id, ods_code_parts=ods_code_parts)

    if tuple(producer_id.split(CUSTODIAN_SEPARATOR)) != ods_code_parts:
        raise RequestValidationError(
            "The target document reference does not belong to the requesting organisation"
        )
    return PipelineData(**data)


def invalid_producer_for_delete(ods_code_parts: tuple[str], delete_item_id: str):
    producer_id, _ = generate_producer_id(id=delete_item_id, producer_id=None)
    return tuple(producer_id.split(CUSTODIAN_SEPARATOR)) != ods_code_parts


@log_action(log_reference=LogReference.COMMON_PRODUCER_APPLY_CONTRACT)
def apply_data_contracts(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    core_model: DocumentPointer = data["core_model"]
    system, value = split_pointer_type(core_model.type.root)
    data_contract_cache: DataContractCache = dependencies[DataContractCache.__name__]
    repository: Repository = dependencies["contract_repository"]
    add_log_fields(type_system=system, type_value=value)

    global_contracts = data_contract_cache.get_global_contracts(logger=logger)
    add_log_fields(global_contracts_cached=global_contracts is not None)
    if not global_contracts:
        global_contracts = get_contracts_from_db(repository=repository, logger=logger)

    local_contracts = data_contract_cache.get(system=system, value=value, logger=logger)
    add_log_fields(local_contracts_cached=local_contracts is not None)
    if not local_contracts:
        local_contracts = get_contracts_from_db(
            repository=repository, system=system, value=value, logger=logger
        )

    data_contract_cache.set_global_contracts(contracts=global_contracts, logger=logger)
    data_contract_cache.set(
        system=system, value=value, contracts=local_contracts, logger=logger
    )

    for contract in (*global_contracts, *local_contracts):
        validate_against_json_schema(
            json_schema=contract.json_schema.root,
            contract_name=contract.full_name,
            instance=core_model._document,
        )
        core_model.schemas.root.append(contract.full_name)

    return PipelineData(**data)
