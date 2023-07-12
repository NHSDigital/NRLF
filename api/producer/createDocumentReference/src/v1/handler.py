from enum import Enum
from functools import partial
from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.constants import LogLevel

from api.producer.createDocumentReference.src.constants import PersistentDependencies
from api.producer.createDocumentReference.src.v1.constants import API_VERSION
from nrlf.core.common_producer_steps import (
    apply_json_schema_validators,
    invalid_producer_for_delete,
)
from nrlf.core.common_steps import (
    make_common_log_action,
    parse_headers,
    read_subject_from_body,
)
from nrlf.core.constants import (
    CUSTODIAN_SEPARATOR,
    PERMISSION_AUDIT_DATES_FROM_PAYLOAD,
    PERMISSION_SUPERSEDE_IGNORE_DELETE_FAIL,
    RELATES_TO_REPLACES,
)
from nrlf.core.dynamodb_types import DynamoDbStringType
from nrlf.core.errors import (
    ItemNotFound,
    ProducerValidationError,
    RequestValidationError,
    SupersedeValidationError,
)
from nrlf.core.event_parsing import fetch_body_from_event
from nrlf.core.model import (
    APIGatewayProxyEventModel,
    DocumentPointer,
    convert_document_pointer_id_to_pk,
)
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

log_action = make_common_log_action()


class LogReference(Enum):
    CREATE_REQUEST = "Parsing request body"
    CREATE_SUPERSEDE_CHECK = "Determining whether document reference will supersede"
    CREATE_SUPERSEDING = "Mark the document for superseding"
    CREATE_PERMISSIONS = "Validating producer permissions"
    CREATE_DB = "Saving document pointer to db"


def _invalid_subject_identifier(
    source_document_pointer: DocumentPointer, target_document_pointer: DocumentPointer
):
    return source_document_pointer.nhs_number != target_document_pointer.nhs_number


def _invalid_type(
    source_document_pointer: DocumentPointer, target_document_pointer: DocumentPointer
):
    return source_document_pointer.type != target_document_pointer.type


def _override_created_on(
    data: PipelineData, document_pointer: DocumentPointer
) -> DocumentPointer:
    fhir_model: StrictDocumentReference = create_fhir_model_from_fhir_json(
        fhir_json=data["body"]
    )
    if fhir_model.date is not None:
        document_pointer.created_on = DynamoDbStringType(__root__=fhir_model.date)

    return document_pointer


@log_action(log_reference=LogReference.CREATE_REQUEST, log_level=LogLevel.DEBUG)
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


@log_action(log_reference=LogReference.CREATE_SUPERSEDING, log_level=LogLevel.DEBUG)
def log_superseded(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    pass


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

    document_relationships = fhir_model.relatesTo

    if document_relationships:
        output["delete_item_ids"] = [
            relationship.target.identifier.value
            for relationship in document_relationships
            if relationship.code == RELATES_TO_REPLACES
        ]
        for id in output["delete_item_ids"]:
            d = {**data, "subject": id}
            log_superseded(d, context, event, dependencies, logger=logger)
    return PipelineData(**data, **output)


@log_action(log_reference=LogReference.CREATE_PERMISSIONS, log_level=LogLevel.DEBUG)
def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    core_model: DocumentPointer = data["core_model"]
    ods_code_parts = data["ods_code_parts"]
    delete_item_ids: list[str] = data.get("delete_item_ids", [])
    pointer_types = data["pointer_types"]

    if ods_code_parts != tuple(
        core_model.producer_id.__root__.split(CUSTODIAN_SEPARATOR)
    ):
        raise ProducerValidationError(
            "The id of the provided document pointer does not include the expected organisation code for this app"
        )

    if ods_code_parts != core_model.custodian_parts:
        raise ProducerValidationError(
            "The custodian of the provided document pointer does not match the expected organisation code for this app"
        )

    if core_model.type.__root__ not in pointer_types:
        raise ProducerValidationError(
            "The type of the provided document pointer is not in the list of allowed types for this app"
        )

    __cannot_delete = partial(invalid_producer_for_delete, ods_code_parts)
    if any(map(__cannot_delete, delete_item_ids)):
        raise RequestValidationError(
            "At least one document pointer cannot be deleted because it belongs to another organisation"
        )

    return PipelineData(**data)


@log_action(log_reference=LogReference.CREATE_SUPERSEDE_CHECK, log_level=LogLevel.DEBUG)
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
    delete_pks = list(
        map(convert_document_pointer_id_to_pk, data.get("delete_item_ids", []))
    )

    confirmed_delete_pks = []

    for delete_pk in delete_pks:
        has_delete_target, target_delete_pk = _validate_ok_to_supersede(
            document_pointer_repository, source_document_pointer, delete_pk, data
        )

        if has_delete_target:
            confirmed_delete_pks.append(target_delete_pk)

    return PipelineData(**data, delete_pks=confirmed_delete_pks)


def _validate_ok_to_supersede(
    document_pointer_repository: Repository,
    source_document_pointer: DocumentPointer,
    delete_pk: str,
    data: PipelineData,
) -> tuple[bool, str]:
    ignore_delete_error = (
        PERMISSION_SUPERSEDE_IGNORE_DELETE_FAIL in data["nrl_permissions"]
    )
    has_delete_target = True

    try:
        document_to_delete: DocumentPointer = document_pointer_repository.read_item(
            delete_pk
        )
    except ItemNotFound:
        if ignore_delete_error:
            has_delete_target = False
            return has_delete_target, delete_pk
        else:
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

    return has_delete_target, delete_pk


@log_action(log_reference=LogReference.CREATE_DB, log_level=LogLevel.DEBUG)
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
    delete_pks: list[str] = data.get("delete_pks", [])

    if PERMISSION_AUDIT_DATES_FROM_PAYLOAD in data["nrl_permissions"]:
        core_model = _override_created_on(data=data, document_pointer=core_model)

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
    read_subject_from_body,
    parse_headers,
    parse_request_body,
    apply_json_schema_validators,
    mark_as_supersede,
    validate_producer_permissions,
    validate_ok_to_supersede,
    save_core_model_to_db,
]
