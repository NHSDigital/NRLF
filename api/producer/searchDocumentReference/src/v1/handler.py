import json
import resource
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from nrlf.core.errors import AuthenticationError
from nrlf.core.model import BundleEntry, DocumentPointer
from nrlf.core.query import create_read_and_filter_query
from nrlf.core.repository import Repository
from nrlf.core.transform import create_bundle_from_document_pointers
from nrlf.producer.fhir.r4.model import Bundle, DocumentReference

from api.producer.searchDocumentReference.src.constants import PersistentDependencies


def _is_valid_producer():
    # TODO: mocked out due to not knowing authentication method
    return True


def _producer_exists():
    # TODO: mocked out due to not knowing authentication method
    return True


def validate_producer_permissions(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    if not _producer_exists():
        raise AuthenticationError("Custodian does not exist in the system")

    if not _is_valid_producer():
        raise AuthenticationError(
            "Required permission to create a document pointer are missing"
        )
    return PipelineData(**data)


def parse_client_rp_details(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:
    client_rp_details = json.loads(event.headers["NHSD-Client-RP-Details"])
    return PipelineData(
        producer_id=client_rp_details["app.ASID"],
        pointer_types=client_rp_details["nrl.pointer-types"],
        **data,
    )


def search_document_references(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
) -> PipelineData:

    repository: Repository = dependencies["repository"]

    search_and_filter_query = create_read_and_filter_query(
        nhs_number=event.queryStringParameters["subject"],
        producer_id=data["producer_id"],
        type=data["pointer_types"],
    )

    document_pointers: list[DocumentPointer] = repository.search(
        index_name=PersistentDependencies.NHS_NUMBER_INDEX, **search_and_filter_query
    )

    bundle = create_bundle_from_document_pointers(document_pointers)
    return PipelineData(bundle)


steps = [
    parse_client_rp_details,
    validate_producer_permissions,
    search_document_references,
]
