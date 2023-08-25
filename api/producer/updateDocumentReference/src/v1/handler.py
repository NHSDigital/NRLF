from enum import Enum
from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData

from api.producer.updateDocumentReference.src.constants import PersistentDependencies
from api.producer.updateDocumentReference.src.v1.constants import (
    API_VERSION,
    IMMUTABLE_FIELDS,
)
from nrlf.core.common_producer_steps import (
    apply_data_contracts,
    validate_producer_permissions,
)
from nrlf.core.common_steps import (
    make_common_log_action,
    parse_headers,
    parse_path_id,
    read_subject_from_path,
)
from nrlf.core.errors import ImmutableFieldViolationError, InconsistentUpdateId
from nrlf.core.event_parsing import fetch_body_from_event
from nrlf.core.model import APIGatewayProxyEventModel, DocumentPointer
from nrlf.core.nhsd_codings import NrlfCoding
from nrlf.core.repository import Repository
from nrlf.core.response import operation_outcome_ok
from nrlf.core.transform import update_document_pointer_from_fhir_json
from nrlf.core.validators import json_loads

log_action = make_common_log_action()


class LogReference(Enum):
    UPDATE001 = "Parsing request body"
    UPDATE002 = "Determining whether document pointer exists"
    UPDATE003 = "Comparing immutable fields"
    UPDATE004 = "Updating document pointer model in db"


@log_action(log_reference=LogReference.UPDATE001)
def parse_request_body(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    body = fetch_body_from_event(event)

    if ("id" in body and "id" in data) and (body["id"] != data["id"]):
        raise InconsistentUpdateId(
            "Existing document id does not match the document id in the body"
        )

    core_model = update_document_pointer_from_fhir_json(body, API_VERSION)
    return PipelineData(core_model=core_model, **data)


@log_action(log_reference=LogReference.UPDATE002)
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


def _sort_key(key):
    """
    Sorts lists and dictionaries recursively to enable comparisons of sorted objects.
    Dictionaries are sorted by key, and otherwise lists are sorted by value. Lists of
    dictionaries are sorted by the dictionary key. Dictionaries are transformed into
    lists of tuples, again noting that the output of this function is intended for
    deterministic sorted comparisons.
    """
    if type(key) is list:
        return sorted((_sort_key(k) for k in key), key=_sort_key)
    elif type(key) is dict:
        return [(k, _sort_key(key[k])) for k in sorted(key.keys())]
    return key


def _keys_are_not_equal(a, b):
    return _sort_key(a) != _sort_key(b)


def _validate_immutable_fields(
    a: dict, b: dict, immutable_fields: set = IMMUTABLE_FIELDS
):
    immutable_keys_in_a = immutable_fields.intersection(a.keys())
    immutable_keys_in_b = immutable_fields.intersection(b.keys())
    for k in immutable_keys_in_a | immutable_keys_in_b:
        if _keys_are_not_equal(a.get(k), b.get(k)):
            raise ImmutableFieldViolationError(
                f"Forbidden to update immutable field '{k}'"
            )


@log_action(log_reference=LogReference.UPDATE003)
def compare_immutable_fields(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    core_model = data["core_model"]
    raw_original_document = data["original_document"]
    _validate_immutable_fields(
        a=json_loads(raw_original_document),
        b=json_loads(core_model.document.__root__),
    )
    return PipelineData(**data)


@log_action(log_reference=LogReference.UPDATE004)
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
    read_subject_from_path,
    parse_headers,
    parse_path_id,
    parse_request_body,
    apply_data_contracts,
    validate_producer_permissions,
    document_pointer_exists,
    compare_immutable_fields,
    update_core_model_to_db,
]
