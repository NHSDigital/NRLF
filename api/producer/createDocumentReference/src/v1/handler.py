from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.event_parsing import fetch_body_from_event
from lambda_utils.header_config import ClientRpDetailsHeader
from nrlf.core.errors import AuthenticationError
from nrlf.core.model import DocumentPointer
from nrlf.core.repository import Repository
from nrlf.core.transform import create_document_pointer_from_fhir_json

from api.producer.createDocumentReference.src.constants import PersistentDependencies
from api.producer.createDocumentReference.src.v1.constants import API_VERSION


def parse_client_rp_details(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    client_rp_details = ClientRpDetailsHeader(event)
    return PipelineData(**data, client_rp_details=client_rp_details)


def parse_request_body(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    body = fetch_body_from_event(event)
    core_model = create_document_pointer_from_fhir_json(body, API_VERSION)
    return PipelineData(**data, core_model=core_model)


def _invalid_producer(
    client_rp_headers: ClientRpDetailsHeader, core_model: DocumentPointer
):
    if not client_rp_headers.custodian == core_model.producer_id.__root__:
        return True

    if core_model.type.__root__ not in client_rp_headers.pointer_types:
        return True

    return False


def _producer_not_exists(client_rp_headers: ClientRpDetailsHeader):
    return not client_rp_headers.custodian


def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    core_model: DocumentPointer = data["core_model"]
    client_rp_details: ClientRpDetailsHeader = data["client_rp_details"]
    if _producer_not_exists(client_rp_details):
        raise AuthenticationError("Custodian does not exist in the system")

    if _invalid_producer(client_rp_details, core_model):
        raise AuthenticationError(
            "Required permission to create a document pointer are missing"
        )
    return PipelineData(**data)


def save_core_model_to_db(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    core_model: DocumentPointer = data["core_model"]
    document_pointer_repository: Repository = dependencies.get(
        PersistentDependencies.DOCUMENT_POINTER_REPOSITORY
    )
    document_pointer_repository.create(core_model)
    return PipelineData(message="Complete")


steps = [
    parse_client_rp_details,
    parse_request_body,
    validate_producer_permissions,
    save_core_model_to_db,
]
