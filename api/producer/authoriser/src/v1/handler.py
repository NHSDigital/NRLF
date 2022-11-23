from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.constants import AUTHORISER_CONTEXT_FIELDS, ApiRequestLevel
from lambda_utils.header_config import ClientRpDetailsHeader
from lambda_utils.logging import log_action

from api.producer.authoriser.src.authoriser_response import authorised_ok


@log_action(narrative="Parsing ClientRpDetails header")
def parse_client_rp_details(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    client_rp_details = ClientRpDetailsHeader(event)
    return PipelineData(client_rp_details=client_rp_details, **data)


@log_action(narrative="Authorising producer request")
def authorise(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    headers = event.headers
    client_rp_details: ClientRpDetailsHeader = data["client_rp_details"]
    context = {
        AUTHORISER_CONTEXT_FIELDS.X_CORRELATION_ID: headers["x-correlation-id"],
        AUTHORISER_CONTEXT_FIELDS.NHSD_CORRELATION_ID: headers["nhsd-correlation-id"],
        AUTHORISER_CONTEXT_FIELDS.REQUEST_TYPE: ApiRequestLevel.APP_RESTRICTED,
        AUTHORISER_CONTEXT_FIELDS.CLIENT_APP_NAME: client_rp_details.developer_app_name,
        AUTHORISER_CONTEXT_FIELDS.CLIENT_APP_ID: client_rp_details.developer_app_id,
    }

    principle_id = context[AUTHORISER_CONTEXT_FIELDS.NHSD_CORRELATION_ID]

    response = authorised_ok(principle_id, data["method_arn"], context)
    return PipelineData(response)


steps = [
    parse_client_rp_details,
    authorise,
]
