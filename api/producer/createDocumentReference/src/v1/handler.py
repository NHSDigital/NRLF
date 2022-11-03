from functools import partial
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.event_parsing import fetch_body_from_event
from lambda_utils.header_config import ClientRpDetailsHeader
from nrlf.core.errors import AuthenticationError
from nrlf.core.model import DocumentPointer
from nrlf.core.repository import Repository
from nrlf.core.transform import (
    create_document_pointer_from_fhir_json,
    create_fhir_model_from_fhir_json,
)
from nrlf.core.validators import generate_producer_id
from nrlf.producer.fhir.r4.strict_model import (
    DocumentReference as StrictDocumentReference,
)

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
    return PipelineData(**data, body=body, core_model=core_model)


def mark_as_supersede(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    fhir_model: StrictDocumentReference = create_fhir_model_from_fhir_json(
        fhir_json=data["body"]
    )

    output = {}
    if fhir_model.relatesTo:
        output["delete_item_ids"] = [
            relatesTo.target.identifier.value
            for relatesTo in fhir_model.relatesTo
            if relatesTo.code == "replaces"
        ]

    return PipelineData(**data, **output)


def _invalid_producer_for_create(
    client_rp_details: ClientRpDetailsHeader, core_model: DocumentPointer
):
    if not client_rp_details.custodian == core_model.producer_id.__root__:
        return True

    if core_model.type.__root__ not in client_rp_details.pointer_types:
        return True

    return False


def _invalid_producer_for_delete(
    client_rp_details: ClientRpDetailsHeader, delete_item_id: str
):
    producer_id = generate_producer_id(id=delete_item_id, producer_id=None)
    if not client_rp_details.custodian == producer_id:
        return True
    return False


def _producer_not_exists(client_rp_details: ClientRpDetailsHeader):
    return not client_rp_details.custodian


def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    core_model: DocumentPointer = data["core_model"]
    client_rp_details: ClientRpDetailsHeader = data["client_rp_details"]
    delete_item_ids: list[str] = data.get("delete_item_ids", [])

    if _producer_not_exists(client_rp_details=client_rp_details):
        raise AuthenticationError("Custodian does not exist in the system")

    if _invalid_producer_for_create(
        client_rp_details=client_rp_details, core_model=core_model
    ):
        raise AuthenticationError(
            "Required permission to create a document pointer are missing"
        )

    __cannot_delete = partial(_invalid_producer_for_delete, client_rp_details)
    if any(map(__cannot_delete, delete_item_ids)):
        raise AuthenticationError(
            "Required permission to delete a document pointer are missing"
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
    delete_item_ids: str = data.get("delete_item_ids")

    if delete_item_ids:
        document_pointer_repository.supersede(
            create_item=core_model,
            delete_item_ids=delete_item_ids,
        )
    else:
        document_pointer_repository.create(item=core_model)
    return PipelineData(message="Complete")


steps = [
    parse_client_rp_details,
    parse_request_body,
    mark_as_supersede,
    validate_producer_permissions,
    save_core_model_to_db,
]
