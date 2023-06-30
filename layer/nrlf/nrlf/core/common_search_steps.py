from enum import Enum
from logging import Logger
from typing import Any, Dict, Optional, Union

from lambda_pipeline.types import FrozenDict, PipelineData
from pydantic import Field
from typing_extensions import Annotated

from layer.nrlf.nrlf.core.constants import DbPrefix
from nrlf.consumer.fhir.r4.model import NextPageToken, RequestQuerySubject
from nrlf.core.common_steps import make_common_log_action
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

log_action = make_common_log_action()


class LogReference(Enum):
    COMMONSEARCH001 = "Searching for document references"


@log_action(log_reference=LogReference.COMMONSEARCH001)
def get_paginated_document_references(
    data: PipelineData,
    requestParams: Union[ConsumerRequestParams, CountRequestParams],
    queryStringParams: Dict[str, str],
    dependencies: FrozenDict[str, Any],
    logger: Logger,
    pageLimit: int = PAGE_ITEM_LIMIT,
    pageToken: Annotated[
        Optional[NextPageToken], Field(alias="next-page-token")
    ] = None,
) -> PipelineData:
    repository: Repository = dependencies["repository"]

    request_params = requestParams

    assert_no_extra_params(
        request_params=request_params, provided_params=queryStringParams
    )

    nhs_number: RequestQuerySubject = request_params.nhs_number

    custodian = None
    if isinstance(requestParams, ConsumerRequestParams):
        custodian = custodian_filter(
            custodian_identifier=request_params.custodian_identifier
        )
        pointer_types = type_filter(
            type_identifier=request_params.type,
            pointer_types=data["pointer_types"],
        )
        validate_type_system(request_params.type, pointer_types=data["pointer_types"])
    else:
        custodian = None
        pointer_types = type_filter(
            type_identifier=None,
            pointer_types=data["pointer_types"],
        )

    if isinstance(requestParams, ConsumerRequestParams):
        if pageToken is None:
            next_page_token: NextPageToken = request_params.next_page_token
        if next_page_token is not None:
            next_page_token = next_page_token.__root__

    else:
        next_page_token: NextPageToken = pageToken

    pk = key(DbPrefix.Patient, nhs_number)

    response: PaginatedResponse = repository.query_gsi_1(
        pk=pk,
        type=pointer_types,
        producer_id=custodian,
        exclusive_start_key=next_page_token,
        limit=pageLimit,
    )

    return response
