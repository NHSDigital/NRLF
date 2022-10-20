from lambda_pipeline.types import PipelineData, LambdaContext, FrozenDict
from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from typing import Any


def handler(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    return PipelineData(message="version two")


steps = [handler]
