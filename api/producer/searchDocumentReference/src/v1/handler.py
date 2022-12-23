from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.logging import log_action
from nrlf.core.common_steps import parse_headers
from nrlf.core.constants import NHS_NUMBER_INDEX
from nrlf.core.errors import assert_no_extra_params
from nrlf.core.model import DocumentPointer, ProducerRequestParams
from nrlf.core.query import create_search_and_filter_query
from nrlf.core.repository import Repository
from nrlf.core.transform import create_bundle_from_document_pointers
from nrlf.producer.fhir.r4.model import RequestQuerySubject


@log_action(narrative="Searching for document references")
def search_document_references(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:

    repository: Repository = dependencies["repository"]
    request_params = ProducerRequestParams(**event.queryStringParameters)
    assert_no_extra_params(
        request_params=request_params, provided_params=event.queryStringParameters
    )

    nhs_number: RequestQuerySubject = request_params.nhs_number

    search_and_filter_query = create_search_and_filter_query(
        nhs_number=nhs_number,
        producer_id=data["organisation_code"],
        type=data["pointer_types"],
    )

    document_pointers: list[DocumentPointer] = repository.search(
        index_name=NHS_NUMBER_INDEX, **search_and_filter_query
    )

    bundle = create_bundle_from_document_pointers(document_pointers)
    return PipelineData(bundle)


steps = [
    parse_headers,
    search_document_references,
]
