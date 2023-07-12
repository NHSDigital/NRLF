from enum import Enum
from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData

from nrlf.consumer.fhir.r4.model import NextPageToken, RequestQuerySubject
from nrlf.core.common_steps import make_common_log_action, parse_headers
from nrlf.core.errors import assert_no_extra_params
from nrlf.core.model import (
    APIGatewayProxyEventModel,
    CountRequestParams,
    PaginatedResponse,
    key,
)
from nrlf.core.repository import COUNT_ITEM_LIMIT, Repository, type_filter
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
    repository: Repository = dependencies["repository"]

    request_params = CountRequestParams(**event.queryStringParameters or {})

    assert_no_extra_params(
        request_params=request_params, provided_params=event.queryStringParameters
    )

    nhs_number: RequestQuerySubject = request_params.nhs_number

    pointer_types = type_filter(
        type_identifier=None,
        pointer_types=data["pointer_types"],
    )

    pk = key("P", nhs_number)

    count = 0
    next_page_token: NextPageToken = None
    while True:
        response: PaginatedResponse = repository.query_gsi_1(
            pk=pk,
            type=pointer_types,
            nhs_number=nhs_number,
            exclusive_start_key=next_page_token,
            limit=COUNT_ITEM_LIMIT,
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
