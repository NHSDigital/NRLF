import json
from typing import Any, List

from aws_lambda_powertools.utilities.parser.models import \
    APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from nrlf.core.errors import AuthenticationError
from nrlf.core.model import DocumentPointer
from nrlf.core.query import create_search_and_filter_query
from nrlf.core.repository import Repository
from nrlf.core.transform import create_bundle_from_document_pointers

from api.consumer.searchDocumentReference.src.constants import \
    PersistentDependencies


def _is_valid_consumer():
    # TODO: Mocked out due to not knowing authentication method
    return True

def _consumer_exists():
    # TODO: Mocked out due to not knowing authentication method
    return True

def validate_consumer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any]
) -> PipelineData:
    if not _consumer_exists():
        raise AuthenticationError("Consumer does not exist in the system")

    if not _is_valid_consumer():
        raise AuthenticationError(
            "Required permission to search for document pointers are missing"
        )

    return PipelineData(**data)

def parse_client_rp_details(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any]
) -> PipelineData:
    client_rp_details = json.loads(event.headers["NHSD-Client-RP-Details"])
    return PipelineData(
        pointer_types=client_rp_details["nrl.pointer-types"],
        **data
    )

def search_document_references(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    repository: Repository = dependencies["repository"]

    search_and_filter_query = create_search_and_filter_query(
        nhs_number=event.queryStringParameters["subject"],
        type=data["pointer_types"]
    )

    document_pointers: List[DocumentPointer] = repository.search(
        index_name=PersistentDependencies.NHS_NUMBER_INDEX,
        **search_and_filter_query
    )

    bundle = create_bundle_from_document_pointers(document_pointers)
    return PipelineData(bundle)


steps = [
    validate_consumer_permissions,
    parse_client_rp_details,
    search_document_references
]
