from enum import Enum
from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData

from nrlf.core.common_search_steps import get_paginated_document_references
from nrlf.core.common_steps import make_common_log_action, parse_headers
from nrlf.core.model import APIGatewayProxyEventModel, ConsumerRequestParams
from nrlf.core.transform import create_bundle_from_paginated_response

log_action = make_common_log_action()


class LogReference(Enum):
    SEARCH001 = "Searching for document references"


@log_action(log_reference=LogReference.SEARCH001)
def search_document_references(
    data: PipelineData,
    event: APIGatewayProxyEventModel,
    context: LambdaContext,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    response = get_paginated_document_references(
        data,
        ConsumerRequestParams(**event.queryStringParameters or {}),
        event.queryStringParameters,
        dependencies,
        logger,
    )
    bundle = create_bundle_from_paginated_response(response)
    return PipelineData(bundle)


steps = [
    parse_headers,
    search_document_references,
]
