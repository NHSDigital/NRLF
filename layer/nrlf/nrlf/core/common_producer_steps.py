from enum import Enum
from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action

from nrlf.core.constants import CUSTODIAN_SEPARATOR
from nrlf.core.errors import RequestValidationError
from nrlf.core.json_schema import JsonSchemaValidatorCache, get_validators_from_db
from nrlf.core.model import (
    APIGatewayProxyEventModel,
    DocumentPointer,
    split_pointer_type,
)
from nrlf.core.repository import Repository
from nrlf.core.validators import generate_producer_id


class LogReference(Enum):
    COMMONPRODUCER001 = "Validating producer permissions"
    COMMONPRODUCER002 = "Applying JSON Schema validator"


@log_action(log_reference=LogReference.COMMONPRODUCER001)
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

    if tuple(producer_id.split(CUSTODIAN_SEPARATOR)) != ods_code_parts:
        raise RequestValidationError(
            "The target document reference does not belong to the requesting organisation"
        )
    return PipelineData(**data)


def invalid_producer_for_delete(ods_code_parts: tuple[str], delete_item_id: str):
    producer_id, _ = generate_producer_id(id=delete_item_id, producer_id=None)
    return tuple(producer_id.split(CUSTODIAN_SEPARATOR)) != ods_code_parts


@log_action(log_reference=LogReference.COMMONPRODUCER002)
def apply_json_schema_validators(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    core_model: DocumentPointer = data["core_model"]
    system, value = split_pointer_type(core_model.type.__root__)
    json_schema_validator_cache: JsonSchemaValidatorCache = dependencies[
        "json_schema_validator_cache"
    ]
    repository: Repository = dependencies["contract_repository"]

    global_validators = json_schema_validator_cache.get_global_validators(
        logger=logger
    ) or get_validators_from_db(repository=repository, logger=logger)

    validators = json_schema_validator_cache.get(
        system=system, value=value, logger=logger
    ) or get_validators_from_db(
        repository=repository, system=system, value=value, logger=logger
    )

    json_schema_validator_cache.set_global_validators(
        validators=global_validators, logger=logger
    )
    json_schema_validator_cache.set(
        system=system, value=value, validators=validators, logger=logger
    )

    for validator in (*global_validators, *validators):
        validator(core_model._document)

    return PipelineData(**data)
