import json
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from nrlf.core.model import DocumentPointer
from nrlf.core.query import create_read_and_filter_query
from nrlf.core.repository import Repository


def parse_client_rp_details(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    client_rp_details = json.loads(event.headers["NHSD-Client-RP-Details"])
    return PipelineData(
        producer_id=client_rp_details["app.ASID"],
        pointer_types=client_rp_details["nrl.pointer-types"],
        **data,
    )


def read_document_reference(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    read_and_filter_query = create_read_and_filter_query(
        id=event.pathParameters["id"],
        producer_id=data["producer_id"],
        type=data["pointer_types"],
    )
    document_pointer: DocumentPointer = repository.read(**read_and_filter_query)
    return PipelineData(**json.loads(document_pointer.document.__root__))


steps = [parse_client_rp_details, read_document_reference]
