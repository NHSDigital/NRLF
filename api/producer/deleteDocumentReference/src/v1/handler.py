import urllib.parse
from enum import Enum
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action
from nrlf.core.common_steps import parse_headers, parse_path_id
from nrlf.core.errors import AuthenticationError
from nrlf.core.model import DocumentPointer
from nrlf.core.nhsd_codings import NrlfCoding
from nrlf.core.repository import Repository
from nrlf.core.response import operation_outcome_ok
from nrlf.core.validators import generate_producer_id


class LogReference(Enum):
    DELETE001 = "Validating producer permissions"
    DELETE002 = "Validating item exists for deletion"
    DELETE003 = "Deleting document reference"


def _invalid_producer_for_delete(organisation_code, delete_item_id: str):
    producer_id = generate_producer_id(id=delete_item_id, producer_id=None)
    if not organisation_code == producer_id:
        return True
    return False


@log_action(log_reference=LogReference.DELETE001)
def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    organisation_code = data["organisation_code"]
    decoded_id = urllib.parse.unquote(event.pathParameters["id"])

    if _invalid_producer_for_delete(
        organisation_code=organisation_code, delete_item_id=decoded_id
    ):
        raise AuthenticationError(
            "Required permissions to delete a document pointer are missing"
        )

    return PipelineData(decoded_id=decoded_id, **data)


@log_action(log_reference=LogReference.DELETE002)
def validate_item_exists(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    decoded_id = data["decoded_id"]
    pk = DocumentPointer.convert_id_to_pk(decoded_id)

    repository: Repository = dependencies["repository"]
    repository.read_item(pk)

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

    repository.hard_delete(pk, pk)

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
