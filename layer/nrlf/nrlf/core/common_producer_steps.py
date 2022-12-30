from logging import Logger
from multiprocessing import AuthenticationError
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action


@log_action(narrative="Validating producer permissions")
def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:

    # Compare producer id from path id to ods code from NHSD-Connection-Metadata
    producer_id = data["producer_id"]
    organisation_code = data["organisation_code"]

    if producer_id != organisation_code:
        raise AuthenticationError(
            "Required permissions to create a document pointer are missing"
        )
    return PipelineData(**data)
