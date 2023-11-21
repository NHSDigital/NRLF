from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData

from nrlf.consumer.fhir.r4.model import NextPageToken
from nrlf.core.common_search_steps import get_paginated_document_references
from nrlf.core.common_steps import make_common_log_action, parse_headers
from nrlf.core.model import (
    APIGatewayProxyEventModel,
    CountRequestParams,
    PaginatedResponse,
)
from nrlf.core.repository import COUNT_ITEM_LIMIT, Repository
from nrlf.core.transform import create_bundle_count
from nrlf.log_references import LogReference

log_action = make_common_log_action()


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
    repository: Repository = dependencies["repository"]

    request_params = CountRequestParams(**event.queryStringParameters or {})

    while True:
        response: PaginatedResponse = get_paginated_document_references(
            request_params=request_params,
            query_string_params=event.queryStringParameters,
            repository=repository,
            type_identifier=None,
            raw_pointer_types=data["pointer_types"],
            nhs_number=request_params.nhs_number,
            page_limit=COUNT_ITEM_LIMIT,
            page_token=next_page_token,
        )
        count = count + len(response.items)
        next_page_token = response.last_evaluated_key
        if next_page_token is None:
            break

    bundle = create_bundle_count(count)
    return PipelineData(bundle)


steps = [
    parse_headers,
    search_document_references,
]
