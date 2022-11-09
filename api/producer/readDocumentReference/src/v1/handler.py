import json
import urllib.parse
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.header_config import ClientRpDetailsHeader
from lambda_utils.logging import log_action
from nrlf.core.model import DocumentPointer
from nrlf.core.query import create_read_and_filter_query
from nrlf.core.repository import Repository


@log_action(narrative="Parsing producer permissions")
def parse_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    client_rp_details = ClientRpDetailsHeader(event)
    return PipelineData(
        client_rp_details=client_rp_details,
        **data,
    )


@log_action(narrative="Reading document reference")
def read_document_reference(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    client_rp_details: ClientRpDetailsHeader = data["client_rp_details"]
    decoded_id = urllib.parse.unquote(event.pathParameters["id"])
    read_and_filter_query = create_read_and_filter_query(
        id=decoded_id,
        producer_id=client_rp_details.custodian,
        type=client_rp_details.pointer_types,
    )
    document_pointer: DocumentPointer = repository.read(**read_and_filter_query)
    return PipelineData(**json.loads(document_pointer.document.__root__))


steps = [parse_producer_permissions, read_document_reference]
