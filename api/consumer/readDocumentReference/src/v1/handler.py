import json
import urllib.parse
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action
from nrlf.core.model import DocumentPointer
from nrlf.core.query import create_read_and_filter_query
from nrlf.core.repository import Repository


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
    pointer_types = json.loads(event.requestContext.authorizer.claims["pointer_types"])
    read_and_filter_query = create_read_and_filter_query(
        id=decoded_id, type=pointer_types
    )
    document_pointer: DocumentPointer = repository.read(**read_and_filter_query)
    return PipelineData(**json.loads(document_pointer.document.__root__))


steps = [read_document_reference]
