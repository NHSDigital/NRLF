from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.header_config import ClientRpDetailsHeader
from nrlf.core.model import DocumentPointer, ProducerRequestParams
from nrlf.core.query import create_search_and_filter_query
from nrlf.core.repository import Repository
from nrlf.core.transform import create_bundle_from_document_pointers
from nrlf.producer.fhir.r4.model import RequestQuerySubject

from api.producer.searchDocumentReference.src.constants import PersistentDependencies


def parse_client_rp_details(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    client_rp_details = ClientRpDetailsHeader(event)

    return PipelineData(
        client_rp_details=client_rp_details,
        **data,
    )


def search_document_references(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:

    repository: Repository = dependencies["repository"]
    client_rp_details: ClientRpDetailsHeader = data["client_rp_details"]

    request_params = ProducerRequestParams(**event.queryStringParameters)
    nhs_number: RequestQuerySubject = request_params.nhs_number

    search_and_filter_query = create_search_and_filter_query(
        nhs_number=nhs_number,
        producer_id=client_rp_details.custodian,
        type=client_rp_details.pointer_types,
    )

    document_pointers: list[DocumentPointer] = repository.search(
        index_name=PersistentDependencies.NHS_NUMBER_INDEX, **search_and_filter_query
    )

    bundle = create_bundle_from_document_pointers(document_pointers)
    return PipelineData(bundle)


steps = [
    parse_client_rp_details,
    search_document_references,
]
