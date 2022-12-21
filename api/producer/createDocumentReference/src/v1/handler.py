import json
from functools import partial
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.event_parsing import fetch_body_from_event
from lambda_utils.header_config import AuthHeader
from lambda_utils.logging import log_action
from nrlf.core.errors import AuthenticationError
from nrlf.core.model import DocumentPointer
from nrlf.core.nhsd_codings import NrlfCoding
from nrlf.core.repository import Repository
from nrlf.core.response import operation_outcome_ok
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


def _invalid_producer_for_create(
    organisation_code,
    core_model: DocumentPointer,
    pointer_types,
):
    return (organisation_code != core_model.producer_id.__root__) or (
        core_model.type.__root__ not in pointer_types
    )


def _invalid_producer_for_delete(organisation_code, delete_item_id: str):
    producer_id = generate_producer_id(id=delete_item_id, producer_id=None)
    if not organisation_code == producer_id:
        return True
    return False


@log_action(narrative="Parsing headers")
def parse_headers(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    organisation_code = AuthHeader(**event.headers).organisation_code
    return PipelineData(**data, organisation_code=organisation_code)


@log_action(narrative="Parsing request body")
def parse_request_body(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    body = fetch_body_from_event(event)
    core_model = create_document_pointer_from_fhir_json(body, API_VERSION)
    return PipelineData(**data, body=body, core_model=core_model)


@log_action(narrative="Determining whether document reference will supersede")
def mark_as_supersede(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
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


@log_action(narrative="Validating producer permissions")
def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    core_model: DocumentPointer = data["core_model"]
    pointer_types = json.loads(event.requestContext.authorizer.claims["pointer_types"])
    organisation_code = data["organisation_code"]
    delete_item_ids: list[str] = data.get("delete_item_ids", [])

    if _invalid_producer_for_create(
        organisation_code=organisation_code,
        core_model=core_model,
        pointer_types=pointer_types,
    ):
        raise AuthenticationError(
            "Required permissions to create a document pointer are missing"
        )

    __cannot_delete = partial(_invalid_producer_for_delete, organisation_code)

    if any(map(__cannot_delete, delete_item_ids)):
        raise AuthenticationError(
            "Required permissions to delete a document pointer are missing"
        )

    return PipelineData(**data)


@log_action(narrative="Saving document pointer to db")
def save_core_model_to_db(
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
    delete_item_ids: str = data.get("delete_item_ids")

    if delete_item_ids:
        document_pointer_repository.supersede(
            create_item=core_model,
            delete_item_ids=delete_item_ids,
        )
        coding = NrlfCoding.RESOURCE_SUPERSEDED
    else:
        document_pointer_repository.create(item=core_model)
        coding = NrlfCoding.RESOURCE_CREATED
    operation_outcome = operation_outcome_ok(
        transaction_id=logger.transaction_id, coding=coding
    )
    return PipelineData(**operation_outcome)


steps = [
    parse_headers,
    parse_request_body,
    mark_as_supersede,
    validate_producer_permissions,
    save_core_model_to_db,
]
