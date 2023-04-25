from enum import Enum
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action
from nrlf.core.common_steps import parse_headers, parse_path_id
from nrlf.core.model import DocumentPointer
from nrlf.core.repository import Repository
from nrlf.core.validators import json_loads, validate_document_reference_string


class LogReference(Enum):
    READ001 = "Reading document reference"


@log_action(log_reference=LogReference.READ001)
def read_document_reference(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    pointer_types = data["pointer_types"]

    document_pointer: DocumentPointer = repository.read_item(
        data["pk"], type=pointer_types
    )

    validate_document_reference_string(document_pointer.document.__root__)

    return PipelineData(**json_loads(document_pointer.document.__root__))


steps = [
    parse_headers,
    parse_path_id,
    read_document_reference,
]
