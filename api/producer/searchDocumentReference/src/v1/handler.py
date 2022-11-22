from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.header_config import ClientRpDetailsHeader
from lambda_utils.logging import log_action
from nrlf.core.model import DocumentPointer, ProducerRequestParams
from nrlf.core.query import create_search_and_filter_query
from nrlf.core.repository import Repository
from nrlf.core.transform import (
    create_bundle_from_document_pointers,
    pagination_parameters,
)
from nrlf.producer.fhir.r4.model import RequestQuerySubject

from api.producer.searchDocumentReference.src.constants import PersistentDependencies


@log_action(narrative="Parsing ClientRpDetails header")
def parse_client_rp_details(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    client_rp_details = ClientRpDetailsHeader(event)

    return PipelineData(
        client_rp_details=client_rp_details,
        **data,
    )


@log_action(narrative="Searching for document references")
def search_document_references(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:

    repository: Repository = dependencies["repository"]
    client_rp_details: ClientRpDetailsHeader = data["client_rp_details"]

    request_params = ProducerRequestParams(**event.queryStringParameters)
    nhs_number: RequestQuerySubject = request_params.nhs_number
    pagination = pagination_parameters(**event.queryStringParameters)

    search_and_filter_query = create_search_and_filter_query(
        nhs_number=nhs_number,
        pagesize=pagination["pagesize"],
        order=pagination["order"],
        producer_id=client_rp_details.custodian,
        type=client_rp_details.pointer_types,
    )

    document_pointers: list[DocumentPointer] = repository.search(
        index_name=PersistentDependencies.NHS_NUMBER_INDEX,
        required_page=pagination["page"],
        **search_and_filter_query,
    )

    bundle = create_bundle_from_document_pointers(document_pointers)
    return PipelineData(bundle)


steps = [
    parse_client_rp_details,
    search_document_references,
]
