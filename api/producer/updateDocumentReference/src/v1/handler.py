import json
import urllib.parse
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.event_parsing import fetch_body_from_event
from lambda_utils.header_config import ConnectionMetadata
from lambda_utils.logging import log_action
from nrlf.core.common_producer_steps import validate_producer_permissions
from nrlf.core.common_steps import parse_headers, parse_path_id
from nrlf.core.errors import (
    AuthenticationError,
    ImmutableFieldViolationError,
    RequestValidationError,
)
from nrlf.core.model import DocumentPointer
from nrlf.core.nhsd_codings import NrlfCoding
from nrlf.core.query import create_read_and_filter_query, update_and_filter_query
from nrlf.core.repository import Repository
from nrlf.core.response import operation_outcome_ok
from nrlf.core.transform import update_document_pointer_from_fhir_json

from api.producer.updateDocumentReference.src.constants import PersistentDependencies
from api.producer.updateDocumentReference.src.v1.constants import (
    API_VERSION,
    IMMUTABLE_FIELDS,
)


@log_action(narrative="Parsing request body")
def parse_request_body(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    body = fetch_body_from_event(event)

    if ("id" in body and "id" in data) and (body["id"] is not data["id"]):
        raise RequestValidationError("The path id and body id must match")

    core_model = update_document_pointer_from_fhir_json(body, API_VERSION)
    return PipelineData(core_model=core_model, **data)


@log_action(narrative="Determining whether document pointer exists")
def document_pointer_exists(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository: Repository = dependencies["document_pointer_repository"]

    pk = data["pk"]

    document_pointer: DocumentPointer = repository.read_item(pk)

    return PipelineData(
        original_document=document_pointer.document.__root__,
        **data,
    )


@log_action(narrative="Comparing immutable fields")
def compare_immutable_fields(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    core_model = data["core_model"]
    original_document = json.loads(data["original_document"])
    updated_document = json.loads(core_model.document.__root__)
    for k in IMMUTABLE_FIELDS.intersection(updated_document.keys()):
        if updated_document[k] != original_document.get(k):
            raise ImmutableFieldViolationError(
                "Trying to update one or more immutable fields"
            )

    return PipelineData(**data)


@log_action(narrative="Updating document pointer model in db")
def update_core_model_to_db(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    core_model: DocumentPointer = data["core_model"]
    document_pointer_repository: Repository = dependencies.get(
        PersistentDependencies.DOCUMENT_POINTER_REPOSITORY
    )
    document_pointer_repository.update(item=core_model)

    operation_outcome = operation_outcome_ok(
        transaction_id=logger.transaction_id, coding=NrlfCoding.RESOURCE_UPDATED
    )
    return PipelineData(**operation_outcome)


steps = [
    parse_headers,
    parse_path_id,
    parse_request_body,
    validate_producer_permissions,
    document_pointer_exists,
    compare_immutable_fields,
    update_core_model_to_db,
]
