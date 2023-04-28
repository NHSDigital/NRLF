from enum import Enum
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action
from nrlf.core.common_steps import parse_headers
from nrlf.core.constants import DbPrefix
from nrlf.core.errors import assert_no_extra_params
from nrlf.core.event_parsing import fetch_body_from_event
from nrlf.core.model import PaginatedResponse, ProducerRequestParams, key
from nrlf.core.repository import Repository, type_filter
from nrlf.core.transform import create_bundle_from_paginated_response
from nrlf.core.validators import validate_type_system
from nrlf.producer.fhir.r4.model import NextPageToken, RequestQuerySubject


class LogReference(Enum):
    SEARCHPOST001 = "Searching for document references"


@log_action(log_reference=LogReference.SEARCHPOST001)
def search_document_references(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:

    repository: Repository = dependencies["repository"]
    body = fetch_body_from_event(event)
    request_params = ProducerRequestParams(**body)
    assert_no_extra_params(request_params=request_params, provided_params=body)
    nhs_number: RequestQuerySubject = request_params.nhs_number
    ods_code_parts = data["ods_code_parts"]

    validate_type_system(request_params.type, pointer_types=data["pointer_types"])

    pointer_types = type_filter(
        type_identifier=request_params.type,
        pointer_types=data["pointer_types"],
    )

    next_page_token: NextPageToken = request_params.next_page_token

    if next_page_token is not None:
        next_page_token = next_page_token.__root__

    response: PaginatedResponse = repository.query_gsi_2(
        pk=key(DbPrefix.Organization, *ods_code_parts),
        type=pointer_types,
        nhs_number=nhs_number,
        exclusive_start_key=next_page_token,
    )

    bundle = create_bundle_from_paginated_response(response)
    return PipelineData(bundle)


steps = [
    parse_headers,
    search_document_references,
]
