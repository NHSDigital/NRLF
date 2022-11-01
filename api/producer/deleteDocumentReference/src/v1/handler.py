import json
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from nrlf.core.model import DocumentPointer
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


def delete_document_reference(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    document_reference_id = event.pathParameters["id"]
    repository.hard_delete(id={"S": f"{document_reference_id}"})
    return PipelineData(message="Resource removed")


steps = [parse_client_rp_details, delete_document_reference]
