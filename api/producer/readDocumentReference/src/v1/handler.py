import urllib.parse
from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import add_log_fields

from nrlf.core.common_steps import (
    make_common_log_action,
    parse_headers,
    parse_path_id,
    read_subject_from_path,
)
from nrlf.core.constants import CUSTODIAN_SEPARATOR
from nrlf.core.errors import RequestValidationError
from nrlf.core.model import APIGatewayProxyEventModel, DocumentPointer
from nrlf.core.repository import Repository
from nrlf.core.validators import (
    generate_producer_id,
    json_loads,
    validate_document_reference_string,
)
from nrlf.log_references import LogReference

log_action = make_common_log_action()


def _invalid_producer_for_read(ods_code_parts, read_item_id: str):
    producer_id, _ = generate_producer_id(id=read_item_id, producer_id=None)
    if not ods_code_parts == tuple(producer_id.split(CUSTODIAN_SEPARATOR)):
        return True
    return False


@log_action(log_reference=LogReference.READ001)
def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    ods_code_parts = data["ods_code_parts"]
    decoded_id = urllib.parse.unquote(event.pathParameters["id"])
    add_log_fields(ods_code_parts=ods_code_parts, decoded_id=decoded_id)

    if _invalid_producer_for_read(
        ods_code_parts=ods_code_parts, read_item_id=decoded_id
    ):
        raise RequestValidationError(
            "The requested document pointer cannot be read because it belongs to another organisation"
        )

    return PipelineData(decoded_id=decoded_id, **data)


@log_action(log_reference=LogReference.READ002)
def read_document_reference(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    document_pointer: DocumentPointer = repository.read_item(data["pk"])
    add_log_fields(pointer_id=document_pointer.id)

    validate_document_reference_string(document_pointer.document.__root__)

    return PipelineData(**json_loads(document_pointer.document.__root__))


steps = [
    read_subject_from_path,
    parse_headers,
    parse_path_id,
    validate_producer_permissions,
    read_document_reference,
]
