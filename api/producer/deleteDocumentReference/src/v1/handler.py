import json
import urllib.parse
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.header_config import AuthHeader
from lambda_utils.logging import log_action
from nrlf.core.errors import AuthenticationError
from nrlf.core.nhsd_codings import NrlfCoding
from nrlf.core.query import create_read_and_filter_query, hard_delete_query
from nrlf.core.repository import Repository
from nrlf.core.response import operation_outcome_ok
from nrlf.core.validators import generate_producer_id


@log_action(narrative="Parsing headers")
def parse_headers(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    organisation_code = AuthHeader(**event.headers).organisation_code

    pointer_types = json.loads(event.requestContext.authorizer.claims["pointer_types"])
    return PipelineData(
        **data, organisation_code=organisation_code, pointer_types=pointer_types
    )


def _invalid_producer_for_delete(organisation_code, delete_item_id: str):
    producer_id = generate_producer_id(id=delete_item_id, producer_id=None)
    if not organisation_code == producer_id:
        return True
    return False


@log_action(narrative="Validating producer permissions")
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


@log_action(narrative="Validating item exists for deletion")
def validate_item_exists(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:

    organisation_code = data["organisation_code"]
    decoded_id = data["decoded_id"]
    pointer_types = data["pointer_types"]

    read_and_filter_query = create_read_and_filter_query(
        id=decoded_id,
        producer_id=organisation_code,
        type=pointer_types,
    )

    repository: Repository = dependencies["repository"]
    repository.read(**read_and_filter_query)

    return PipelineData(**data)


@log_action(narrative="Deleting document reference")
def delete_document_reference(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    pointer_types = json.loads(event.requestContext.authorizer.claims["pointer_types"])

    query = hard_delete_query(id=data["decoded_id"], type=pointer_types)
    repository.hard_delete(**query)

    operation_outcome = operation_outcome_ok(
        transaction_id=logger.transaction_id, coding=NrlfCoding.RESOURCE_REMOVED
    )
    return PipelineData(**operation_outcome)


steps = [
    parse_headers,
    validate_producer_permissions,
    validate_item_exists,
    delete_document_reference,
]
