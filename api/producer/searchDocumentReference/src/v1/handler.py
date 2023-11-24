from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import add_log_fields

from nrlf.core.common_steps import make_common_log_action, parse_headers
from nrlf.core.constants import DbPrefix
from nrlf.core.errors import assert_no_extra_params
from nrlf.core.model import (
    APIGatewayProxyEventModel,
    PaginatedResponse,
    ProducerRequestParams,
    key,
)
from nrlf.core.repository import Repository, type_filter
from nrlf.core.transform import create_bundle_from_paginated_response
from nrlf.core.validators import validate_type_system
from nrlf.log_references import LogReference
from nrlf.producer.fhir.r4.model import NextPageToken

log_action = make_common_log_action()


@log_action(log_reference=LogReference.SEARCH001)
def search_document_references(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    repository: Repository = dependencies["repository"]
    request_params = ProducerRequestParams(**event.queryStringParameters or {})

    assert_no_extra_params(
        request_params=request_params, provided_params=event.queryStringParameters
    )

    nhs_number = request_params.nhs_number

    ods_code_parts = data["ods_code_parts"]

    add_log_fields(
        ods_code_parts=ods_code_parts,
        incoming_pointer_types=data["pointer_types"],
        type_identifier=request_params.type,
        nhs_number=nhs_number,
    )

    validate_type_system(request_params.type, pointer_types=data["pointer_types"])

    pointer_types = type_filter(
        type_identifier=request_params.type,
        pointer_types=data["pointer_types"],
    )

    add_log_fields(
        pointer_types=pointer_types,
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
    add_log_fields(items_found=bundle.total)
    return PipelineData(bundle)


steps = [
    parse_headers,
    search_document_references,
]
