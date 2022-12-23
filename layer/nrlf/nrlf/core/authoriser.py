import json
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.constants import CLIENT_RP_DETAILS, CONNECTION_METADATA
from lambda_utils.header_config import (
    AbstractHeader,
    ClientRpDetailsHeader,
    ConnectionMetadata,
)
from lambda_utils.logging import log_action
from nrlf.core.response import get_error_message
from pydantic import ValidationError


def _create_policy(principal_id, resource, effect, context):
    return {
        "principalId": principal_id,
        "context": context,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "execute-api:Invoke", "Effect": effect, "Resource": resource}
            ],
        },
    }


@log_action(narrative="Parsing headers")
def parse_headers(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    _headers = AbstractHeader(**event.headers).headers
    _raw_client_rp_details = _headers.get(CLIENT_RP_DETAILS, "{}")
    _raw_connection_metadata = _headers.get(CONNECTION_METADATA, "{}")
    try:
        connection_metadata = ConnectionMetadata.parse_raw(_raw_connection_metadata)
        ClientRpDetailsHeader.parse_raw(_raw_client_rp_details)
    except ValidationError as err:
        return PipelineData(error={"message": get_error_message(err)}, **data)
    else:
        return PipelineData(pointer_types=connection_metadata.pointer_types, **data)


@log_action(narrative="Validating pointer types")
def validate_pointer_types(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    if data.get("pointer_types") == []:
        return PipelineData(
            error={"message": "No pointer types have been provided"}, **data
        )
    return PipelineData(**data)


@log_action(narrative="Render authorisation response")
def generate_response(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    error = data.get("error")
    policy = _create_policy(
        principal_id=logger.transaction_id,
        resource=data["method_arn"],
        effect="Deny" if error else "Allow",
        context={"error": json.dumps(error)} if error else {},
    )
    return PipelineData(policy)


steps = [
    parse_headers,
    validate_pointer_types,
    generate_response,
]
