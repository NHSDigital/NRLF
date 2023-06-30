from enum import Enum
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData

from layer.nrlf.nrlf.core.common_search_steps import get_paginated_document_references
from nrlf.consumer.fhir.r4.model import NextPageToken
from nrlf.core.common_steps import make_common_log_action, parse_headers
from nrlf.core.model import CountRequestParams, PaginatedResponse
from nrlf.core.repository import COUNT_ITEM_LIMIT
from nrlf.core.transform import create_bundle_count

log_action = make_common_log_action()


class LogReference(Enum):
    SEARCH001 = "Searching for document references"


@log_action(log_reference=LogReference.SEARCH001)
def search_document_references(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:

    count = 0
    next_page_token: NextPageToken = None

    request_params = CountRequestParams(**event.queryStringParameters or {})

    while True:
        response: PaginatedResponse = get_paginated_document_references(
            data,
            request_params,
            event.queryStringParameters,
            dependencies,
            logger,
            COUNT_ITEM_LIMIT,
            next_page_token,
        )
        count = count + len(response.document_pointers)
        next_page_token = response.last_evaluated_key
        if next_page_token is None:
            break

    bundle = create_bundle_count(count)
    return PipelineData(bundle)


steps = [
    parse_headers,
    search_document_references,
]
