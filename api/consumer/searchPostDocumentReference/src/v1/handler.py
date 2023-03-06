from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.event_parsing import fetch_body_from_event
from lambda_utils.logging import log_action
from nrlf.consumer.fhir.r4.model import RequestQueryStartKey, RequestQuerySubject
from nrlf.core.common_steps import parse_headers
from nrlf.core.constants import DbPrefix
from nrlf.core.errors import assert_no_extra_params
from nrlf.core.model import ConsumerRequestParams, PaginatedResponse, key
from nrlf.core.repository import Repository, custodian_filter, type_filter
from nrlf.core.transform import create_bundle_from_paginated_response


@log_action(narrative="Searching for document references")
def search_document_references(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository: Repository = dependencies["repository"]

    body = fetch_body_from_event(event)
    request_params = ConsumerRequestParams(**body)
    assert_no_extra_params(request_params=request_params, provided_params=body)
    nhs_number: RequestQuerySubject = request_params.nhs_number
    pk = key(DbPrefix.Patient, nhs_number)

    custodian = custodian_filter(
        custodian_identifier=request_params.custodian_identifier
    )
    pointer_types = type_filter(
        type_identifier=request_params.type_identifier,
        pointer_types=data["pointer_types"],
    )

    next_page_token: RequestQueryStartKey = request_params.next_page_token

    if next_page_token is not None:
        next_page_token = next_page_token.__root__

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
