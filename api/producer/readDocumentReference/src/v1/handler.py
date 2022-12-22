import json
import urllib.parse
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action
from nrlf.core.common_steps import parse_headers
from nrlf.core.errors import AuthenticationError
from nrlf.core.model import DocumentPointer
from nrlf.core.query import create_read_and_filter_query
from nrlf.core.repository import Repository
from nrlf.core.validators import generate_producer_id


def _invalid_producer_for_read(organisation_code, read_item_id: str):
    producer_id = generate_producer_id(id=read_item_id, producer_id=None)
    if not organisation_code == producer_id:
        return True
    return False


@log_action(narrative="Validating producer permissions")
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
        raise AuthenticationError(
            "Required permissions to read a document pointer are missing"
        )

    return PipelineData(decoded_id=decoded_id, **data)


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
    organisation_code = data["organisation_code"]
    pointer_types = data["pointer_types"]

    read_and_filter_query = create_read_and_filter_query(
        id=decoded_id,
        producer_id=organisation_code,
        type=pointer_types,
    )
    document_pointer: DocumentPointer = repository.read(**read_and_filter_query)
    return PipelineData(**json.loads(document_pointer.document.__root__))


steps = [
    parse_headers,
    validate_producer_permissions,
    read_document_reference,
]
