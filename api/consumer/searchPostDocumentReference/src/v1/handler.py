from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import add_log_fields

from nrlf.core.common_search_steps import get_paginated_document_references
from nrlf.core.common_steps import make_common_log_action, parse_headers
from nrlf.core.event_parsing import fetch_body_from_event
from nrlf.core.model import APIGatewayProxyEventModel, ConsumerRequestParams
from nrlf.core.repository import Repository
from nrlf.core.transform import create_bundle_from_paginated_response
from nrlf.log_references import LogReference

log_action = make_common_log_action()


@log_action(log_reference=LogReference.SEARCHPOST001)
def search_document_references(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:

    body = fetch_body_from_event(event)
    requestParams = ConsumerRequestParams(**body)
    repo: Repository = dependencies["repository"]

    add_log_fields(
        incoming_pointer_types=data["pointer_types"],
        type_identifier=requestParams.type,
        nhs_number=requestParams.nhs_number,
    )

    response = get_paginated_document_references(
        request_params=requestParams,
        query_string_params=body,
        repository=repo,
        type_identifier=requestParams.type,
        raw_pointer_types=data["pointer_types"],
        nhs_number=requestParams.nhs_number,
    )
    bundle = create_bundle_from_paginated_response(response)
    return PipelineData(bundle)


steps = [
    parse_headers,
    search_document_references,
]
