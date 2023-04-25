from enum import Enum
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action
from nrlf.core.common_producer_steps import invalid_producer_for_delete
from nrlf.core.common_steps import parse_headers, parse_path_id
from nrlf.core.errors import RequestValidationError
from nrlf.core.nhsd_codings import NrlfCoding
from nrlf.core.repository import Repository
from nrlf.core.response import operation_outcome_ok


class LogReference(Enum):
    DELETE001 = "Validating producer permissions"
    DELETE002 = "Validating item exists for deletion"
    DELETE003 = "Deleting document reference"


@log_action(log_reference=LogReference.DELETE001)
def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    if invalid_producer_for_delete(
        ods_code_parts=data["ods_code_parts"], delete_item_id=data["id"]
    ):
        raise RequestValidationError(
            "The requested document pointer cannot be deleted because it belongs to another organisation"
        )

    return PipelineData(**data)


@log_action(log_reference=LogReference.DELETE002)
def validate_item_exists(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    repository.read_item(data["pk"])
    return PipelineData(**data)


@log_action(log_reference=LogReference.DELETE003)
def delete_document_reference(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    pk = data["pk"]

    repository.hard_delete(pk=pk, sk=pk)

    operation_outcome = operation_outcome_ok(
        transaction_id=logger.transaction_id, coding=NrlfCoding.RESOURCE_REMOVED
    )
    return PipelineData(**operation_outcome)


steps = [
    parse_headers,
    parse_path_id,
    validate_producer_permissions,
    validate_item_exists,
    delete_document_reference,
]
