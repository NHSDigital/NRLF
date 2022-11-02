import json
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from nrlf.core.dynamodb_types import to_dynamodb_dict
from nrlf.core.model import DocumentPointer
from nrlf.core.query import hard_delete_query
from nrlf.core.repository import Repository


def parse_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    client_rp_details = json.loads(event.headers["NHSD-Client-RP-Details"])
    return PipelineData(
        pointer_types=client_rp_details["nrl.pointer-types"],
        **data,
    )


def delete_document_reference(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    query = hard_delete_query(id=event.pathParameters["id"], type=data["pointer_types"])
    repository.hard_delete(**query)
    return PipelineData(message="Resource removed")


steps = [parse_producer_permissions, delete_document_reference]
