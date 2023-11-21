from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData

from nrlf.core.common_search_steps import get_paginated_document_references
from nrlf.core.common_steps import make_common_log_action, parse_headers
from nrlf.core.model import APIGatewayProxyEventModel, ConsumerRequestParams
from nrlf.core.repository import Repository
from nrlf.core.transform import create_bundle_from_paginated_response
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

    request_params = ConsumerRequestParams(**event.queryStringParameters or {})
    repo: Repository = dependencies["repository"]

    response = get_paginated_document_references(
        request_params=request_params,
        query_string_params=event.queryStringParameters,
        repository=repo,
        type_identifier=request_params.type,
        raw_pointer_types=data["pointer_types"],
        nhs_number=request_params.nhs_number,
    )
    bundle = create_bundle_from_paginated_response(response)
    return PipelineData(bundle)


steps = [
    parse_headers,
    search_document_references,
]
