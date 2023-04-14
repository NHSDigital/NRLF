import urllib.parse
from enum import Enum
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action
from nrlf.core.common_steps import parse_headers, parse_path_id
from nrlf.core.errors import RequestValidationError
from nrlf.core.model import DocumentPointer
from nrlf.core.repository import Repository
from nrlf.core.validators import (
    generate_producer_id,
    json_loads,
    validate_document_reference_string,
)


class LogReference(Enum):
    READ001 = "Validating producer permissions"
    READ002 = "Reading document reference"


def _invalid_producer_for_read(organisation_code, read_item_id: str):
    producer_id, _ = generate_producer_id(id=read_item_id, producer_id=None)
    if not organisation_code == producer_id:
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
    organisation_code = data["organisation_code"]
    decoded_id = urllib.parse.unquote(event.pathParameters["id"])

    if _invalid_producer_for_read(
        organisation_code=organisation_code, read_item_id=decoded_id
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

    validate_document_reference_string(document_pointer.document.__root__)

    return PipelineData(**json_loads(document_pointer.document.__root__))


steps = [
    parse_headers,
    parse_path_id,
    validate_producer_permissions,
    read_document_reference,
]
