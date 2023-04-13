from enum import Enum
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action
from nrlf.core.errors import RequestValidationError
from nrlf.core.validators import generate_producer_id


class LogReference(Enum):
    COMMONPRODUCER001 = "Validating producer permissions"


@log_action(log_reference=LogReference.COMMONPRODUCER001)
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
        raise RequestValidationError(
            "The target document reference does not belong to the requesting organisation"
        )
    return PipelineData(**data)


def invalid_producer_for_delete(organisation_code, delete_item_id: str):
    producer_id = generate_producer_id(id=delete_item_id, producer_id=None)
    return organisation_code != producer_id
