from enum import Enum
from functools import partial
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.event_parsing import fetch_body_from_event
from lambda_utils.logging import log_action
from nrlf.core.common_producer_steps import invalid_producer_for_delete
from nrlf.core.common_steps import parse_headers
from nrlf.core.errors import (
    ItemNotFound,
    ProducerValidationError,
    RequestValidationError,
    SupersedeValidationError,
)
from nrlf.core.model import DocumentPointer
from nrlf.core.nhsd_codings import NrlfCoding
from nrlf.core.repository import Repository
from nrlf.core.response import operation_outcome_ok
from nrlf.core.transform import (
    create_document_pointer_from_fhir_json,
    create_fhir_model_from_fhir_json,
)
from nrlf.producer.fhir.r4.strict_model import (
    DocumentReference as StrictDocumentReference,
)

from api.producer.createDocumentReference.src.constants import PersistentDependencies
from api.producer.createDocumentReference.src.v1.constants import API_VERSION


class LogReference(Enum):
    CREATE001 = "Parsing request body"
    CREATE002 = "Determining whether document reference will supersede"
    CREATE003 = "Validating producer permissions"
    CREATE004 = "Determining whether document reference will supersede"
    CREATE005 = "Saving document pointer to db"


def _invalid_subject_identifier(
    source_document_pointer: DocumentPointer, target_document_pointer: DocumentPointer
):
    return source_document_pointer.nhs_number != target_document_pointer.nhs_number


def _invalid_type(
    source_document_pointer: DocumentPointer, target_document_pointer: DocumentPointer
):
    return source_document_pointer.type != target_document_pointer.type


@log_action(log_reference=LogReference.CREATE001)
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


@log_action(log_reference=LogReference.CREATE002)
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


@log_action(log_reference=LogReference.CREATE003)
def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    core_model: DocumentPointer = data["core_model"]
    organisation_code = data["organisation_code"]
    delete_item_ids: list[str] = data.get("delete_item_ids", [])
    pointer_types = data["pointer_types"]

    if organisation_code != core_model.producer_id.__root__:
        raise ProducerValidationError(
            "The id of the provided document pointer does not include the expected organisation code for this app"
        )

    if organisation_code != core_model.custodian.__root__:
        raise ProducerValidationError(
            "The custodian of the provided document pointer does not match the expected organisation code for this app"
        )

    if core_model.type.__root__ not in pointer_types:
        raise ProducerValidationError(
            "The type of the provided document pointer is not in the list of allowed types for this app"
        )

    __cannot_delete = partial(invalid_producer_for_delete, organisation_code)

    if any(map(__cannot_delete, delete_item_ids)):
        raise RequestValidationError(
            "At least one document pointer cannot be deleted because it belongs to another organisation"
        )

    return PipelineData(**data)


@log_action(log_reference=LogReference.CREATE004)
def validate_ok_to_supersede(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    document_pointer_repository: Repository = dependencies.get(
        PersistentDependencies.DOCUMENT_POINTER_REPOSITORY
    )

    source_document_pointer = data["core_model"]
    delete_item_ids = data.get("delete_item_ids", [])

    delete_pks = map(DocumentPointer.convert_id_to_pk, delete_item_ids)

    for delete_pk in delete_pks:
        _validate_ok_to_supersede(
            document_pointer_repository, source_document_pointer, delete_pk
        )

    return PipelineData(**data)


def _validate_ok_to_supersede(
    document_pointer_repository: Repository,
    source_document_pointer: DocumentPointer,
    delete_pk: str,
):
    try:
        document_to_delete: DocumentPointer = document_pointer_repository.read_item(
            delete_pk
        )
    except (ItemNotFound):
        raise SupersedeValidationError(
            "Validation failure - relatesTo target document does not exist"
        )

    if _invalid_subject_identifier(
        source_document_pointer=source_document_pointer,
        target_document_pointer=document_to_delete,
    ):
        raise SupersedeValidationError(
            "Validation failure - relatesTo target document nhs number does not match the request"
        )

    if _invalid_type(
        source_document_pointer=source_document_pointer,
        target_document_pointer=document_to_delete,
    ):
        raise SupersedeValidationError(
            "Validation failure - relatesTo target document type does not match the request"
        )


@log_action(log_reference=LogReference.CREATE005)
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
    delete_pks = list(
        map(DocumentPointer.convert_id_to_pk, data.get("delete_item_ids", []))
    )
    if delete_pks:
        document_pointer_repository.supersede(
            create_item=core_model, delete_pks=delete_pks
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
    validate_ok_to_supersede,
    save_core_model_to_db,
]
