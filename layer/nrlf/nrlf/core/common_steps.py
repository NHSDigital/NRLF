from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.constants import CONNECTION_METADATA
from lambda_utils.header_config import AbstractHeader, ConnectionMetadata
from lambda_utils.logging import log_action


@log_action(narrative="Parsing headers")
def parse_headers(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    _headers = AbstractHeader(**event.headers).headers
    _raw_connection_metadata = _headers.get(CONNECTION_METADATA, "{}")
    connection_metadata = ConnectionMetadata.parse_raw(_raw_connection_metadata)
    return PipelineData(
        **data,
        organisation_code=connection_metadata.ods_code,
        pointer_types=connection_metadata.pointer_types
    )
