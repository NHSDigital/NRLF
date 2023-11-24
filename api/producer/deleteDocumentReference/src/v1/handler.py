from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import add_log_fields

from nrlf.core.common_producer_steps import invalid_producer_for_delete
from nrlf.core.common_steps import (
    make_common_log_action,
    parse_headers,
    parse_path_id,
    read_subject_from_path,
)
from nrlf.core.errors import RequestValidationError
from nrlf.core.model import APIGatewayProxyEventModel
from nrlf.core.nhsd_codings import NrlfCoding
from nrlf.core.repository import Repository
from nrlf.core.response import operation_outcome_ok
from nrlf.log_references import LogReference

log_action = make_common_log_action()


@log_action(log_reference=LogReference.DELETE001)
def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    add_log_fields(ods_code_parts=data["ods_code_parts"], delete_item_id=data["id"])
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
    add_log_fields(pk=data["pk"])
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
    add_log_fields(pk=pk)

    repository.hard_delete(pk=pk, sk=pk)

    operation_outcome = operation_outcome_ok(
        transaction_id=logger.transaction_id, coding=NrlfCoding.RESOURCE_REMOVED
    )
    return PipelineData(**operation_outcome)


steps = [
    read_subject_from_path,
    parse_headers,
    parse_path_id,
    validate_producer_permissions,
    validate_item_exists,
    delete_document_reference,
]
