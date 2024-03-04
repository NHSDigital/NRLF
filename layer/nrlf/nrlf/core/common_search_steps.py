from typing import Dict, Optional, Union

from lambda_utils.logging import add_log_fields

from nrlf.consumer.fhir.r4.model import (
    NextPageToken,
    RequestQuerySubject,
    RequestQueryType,
)
from nrlf.core.common_steps import make_common_log_action
from nrlf.core.constants import DbPrefix
from nrlf.core.errors import assert_no_extra_params
from nrlf.core.model import (
    ConsumerRequestParams,
    CountRequestParams,
    PaginatedResponse,
    key,
)
from nrlf.core.repository import (
    PAGE_ITEM_LIMIT,
    Repository,
    custodian_filter,
    type_filter,
)
from nrlf.core.validators import validate_type_system
from nrlf.log_references import LogReference

log_action = make_common_log_action()


@log_action(
    log_reference=LogReference.COMMONSEARCH001,
    log_fields=[
        "request_params",
        "query_string_params",
        "nhs_number",
        "type_identifier",
        "raw_pointer_types",
        "page_limit",
    ],
)
def get_paginated_document_references(
    request_params: Union[ConsumerRequestParams, CountRequestParams],
    query_string_params: Dict[str, str],
    repository: Repository,
    type_identifier: RequestQueryType,
    raw_pointer_types: list[str],
    nhs_number: RequestQuerySubject,
    page_limit: int = PAGE_ITEM_LIMIT,
    page_token: Optional[NextPageToken] = None,
) -> PaginatedResponse:

    assert_no_extra_params(
        request_params=request_params, provided_params=query_string_params
    )

    validate_type_system(type_identifier, pointer_types=raw_pointer_types)

    pointer_types = type_filter(
        type_identifier=type_identifier, pointer_types=raw_pointer_types
    )

    custodian = None

    next_page_token: NextPageToken = page_token

    if isinstance(request_params, ConsumerRequestParams):
        custodian = custodian_filter(
            custodian_identifier=request_params.custodian_identifier
        )
        if page_token is None:
            next_page_token: NextPageToken = request_params.next_page_token
        if next_page_token is not None:
            next_page_token = next_page_token.root

    pk = key(DbPrefix.Patient, nhs_number)
    add_log_fields(custodian=custodian, pk=pk, pointer_types=pointer_types)

    response: PaginatedResponse = repository.query_gsi_1(
        pk=pk,
        type=pointer_types,
        producer_id=custodian,
        exclusive_start_key=next_page_token,
        limit=page_limit,
    )
    add_log_fields(count=len(response.items))

    return response
