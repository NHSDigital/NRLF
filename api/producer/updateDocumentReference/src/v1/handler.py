import json
import urllib.parse
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.event_parsing import fetch_body_from_event
from lambda_utils.header_config import ClientRpDetailsHeader
from nrlf.core.errors import AuthenticationError, ImmutableFieldViolationError
from nrlf.core.model import DocumentPointer
from nrlf.core.query import create_read_and_filter_query, update_and_filter_query
from nrlf.core.repository import Repository
from nrlf.core.transform import update_document_pointer_from_fhir_json

from api.producer.updateDocumentReference.src.constants import PersistentDependencies
from api.producer.updateDocumentReference.src.v1.constants import (
    API_VERSION,
    IMMUTABLE_FIELDS,
)


def parse_request_body(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    body = fetch_body_from_event(event)
    core_model = update_document_pointer_from_fhir_json(body, API_VERSION)
    return PipelineData(core_model=core_model)


def parse_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    client_rp_details = ClientRpDetailsHeader(event)
    return PipelineData(
        client_rp_details=client_rp_details,
        **data,
    )


def _is_valid_producer():
    # TODO: mocked out due to not knowing authentication method
    return True


def _producer_exists():
    # TODO: mocked out due to not knowing authentication method
    return True


def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    if not _producer_exists():
        raise AuthenticationError("Custodian does not exist in the system")

    if not _is_valid_producer():
        raise AuthenticationError(
            "Required permission to create a document pointer are missing"
        )
    return PipelineData(**data)


def document_pointer_exists(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    repository: Repository = dependencies["document_pointer_repository"]
    client_rp_details: ClientRpDetailsHeader = data["client_rp_details"]
    decoded_id = urllib.parse.unquote(event.pathParameters["id"])
    read_and_filter_query = create_read_and_filter_query(
        id=decoded_id,
        producer_id=client_rp_details.custodian,
        type=client_rp_details.pointer_types,
    )
    document_pointer: DocumentPointer = repository.read(**read_and_filter_query)
    return PipelineData(
        original_document=document_pointer.document.__root__,
        **data,
    )


def compare_immutable_fields(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
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


def update_core_model_to_db(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    core_model: DocumentPointer = data["core_model"]
    update_query = update_and_filter_query(**core_model.dict())
    document_pointer_repository: Repository = dependencies.get(
        PersistentDependencies.DOCUMENT_POINTER_REPOSITORY
    )
    document_pointer_repository.update(**update_query)
    return PipelineData(message="Resource updated")


steps = [
    parse_request_body,
    parse_producer_permissions,
    validate_producer_permissions,
    document_pointer_exists,
    compare_immutable_fields,
    update_core_model_to_db,
]
