import json
import urllib.parse
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action
from nrlf.core.common_steps import parse_headers
from nrlf.core.model import DocumentPointer
from nrlf.core.repository import Repository
from nrlf.core.validators import validate_document_reference_string


@log_action(narrative="Reading document reference")
def read_document_reference(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    decoded_id = urllib.parse.unquote(event.pathParameters["id"])

    pk = DocumentPointer.convert_id_to_pk(decoded_id)
    pointer_types = data["pointer_types"]

    document_pointer: DocumentPointer = repository.read_item(pk, type=pointer_types)

    validate_document_reference_string(document_pointer.document.__root__)

    return PipelineData(**json.loads(document_pointer.document.__root__))


steps = [
    parse_headers,
    read_document_reference,
]
