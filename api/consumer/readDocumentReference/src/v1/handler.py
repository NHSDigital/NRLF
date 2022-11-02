import json
import urllib.parse
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.header_config import ClientRpDetailsHeader
from nrlf.core.model import DocumentPointer
from nrlf.core.query import create_read_and_filter_query
from nrlf.core.repository import Repository


def parse_consumer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    client_rp_details = ClientRpDetailsHeader(event)
    return PipelineData(
        client_rp_details=client_rp_details,
        **data,
    )


def read_document_reference(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    client_rp_details: ClientRpDetailsHeader = data["client_rp_details"]
    decoded_id = urllib.parse.unquote(event.pathParameters["id"])
    read_and_filter_query = create_read_and_filter_query(
        id=decoded_id, type=client_rp_details.pointer_types
    )
    document_pointer: DocumentPointer = repository.read(**read_and_filter_query)
    return PipelineData(**json.loads(document_pointer.document.__root__))


steps = [parse_consumer_permissions, read_document_reference]
