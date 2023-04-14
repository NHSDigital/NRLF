import urllib.parse
from enum import Enum
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.header_config import AbstractHeader, ConnectionMetadata
from lambda_utils.logging import log_action
from nrlf.core.constants import CONNECTION_METADATA
from nrlf.core.model import convert_document_pointer_id_to_pk


class LogReference(Enum):
    COMMON001 = "Parsing headers"
    COMMON002 = "Parse document pointer id"


@log_action(log_reference=LogReference.COMMON001)
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
        ods_code_parts=connection_metadata.ods_code_parts,
        pointer_types=connection_metadata.pointer_types,
    )


@log_action(log_reference=LogReference.COMMON002)
def parse_path_id(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    """
    Retrieves the {id} from the request path, splits it into different
    representations.
    """
    id = urllib.parse.unquote(event.pathParameters["id"])
    pk = convert_document_pointer_id_to_pk(id)
    return PipelineData(**data, id=id, pk=pk)
