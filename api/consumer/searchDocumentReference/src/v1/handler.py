from enum import Enum
from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData

from nrlf.consumer.fhir.r4.model import NextPageToken, RequestQuerySubject
from nrlf.core.common_steps import make_common_log_action, parse_headers
from nrlf.core.errors import assert_no_extra_params
from nrlf.core.model import (
    APIGatewayProxyEventModel,
    ConsumerRequestParams,
    PaginatedResponse,
    key,
)
from nrlf.core.repository import Repository, custodian_filter, type_filter
from nrlf.core.transform import create_bundle_from_paginated_response
from nrlf.core.validators import validate_type_system

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

    request_params = ConsumerRequestParams(**event.queryStringParameters or {})

    assert_no_extra_params(
        request_params=request_params, provided_params=event.queryStringParameters
    )

    nhs_number: RequestQuerySubject = request_params.nhs_number

    custodian = custodian_filter(
        custodian_identifier=request_params.custodian_identifier
    )

    validate_type_system(request_params.type, pointer_types=data["pointer_types"])

    pointer_types = type_filter(
        type_identifier=request_params.type,
        pointer_types=data["pointer_types"],
    )

    next_page_token: NextPageToken = request_params.next_page_token

    if next_page_token is not None:
        next_page_token = next_page_token.__root__

    pk = key("P", nhs_number)

    response: PaginatedResponse = repository.query_gsi_1(
        pk=pk,
        type=pointer_types,
        producer_id=custodian,
        exclusive_start_key=next_page_token,
    )

    bundle = create_bundle_from_paginated_response(response)
    return PipelineData(bundle)


steps = [
    parse_headers,
    search_document_references,
]
