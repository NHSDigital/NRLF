from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.event_parsing import fetch_body_from_event
from nrlf.core.errors import AuthenticationError
from nrlf.core.model import DocumentPointer
from nrlf.core.repository import Repository
from nrlf.core.transform import create_document_pointer_from_fhir_json

from api.producer.createDocumentReference.src.constants import PersistentDependencies
from api.producer.createDocumentReference.src.v1.constants import API_VERSION


def parse_request_body(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    body = fetch_body_from_event(event)
    core_model = create_document_pointer_from_fhir_json(body, API_VERSION)
    return PipelineData(core_model=core_model)


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


steps = [parse_request_body, validate_producer_permissions, save_core_model_to_db]
