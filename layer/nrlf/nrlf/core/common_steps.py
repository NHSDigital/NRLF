import urllib.parse
from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.header_config import (
    AbstractHeader,
    ClientRpDetailsHeader,
    ConnectionMetadata,
)
from lambda_utils.logging import add_log_fields, log_action, make_scoped_log_action

from nrlf.core.constants import CLIENT_RP_DETAILS, CONNECTION_METADATA
from nrlf.core.model import APIGatewayProxyEventModel, convert_document_pointer_id_to_pk
from nrlf.core.validators import generate_producer_id, json_loads
from nrlf.log_references import LogReference


def read_subject_from_path(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    root = (event.pathParameters or {}).get("id", "unknown")
    subject = root
    return PipelineData(**data, root=root, subject=subject)


def read_subject_from_body(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    try:
        raw = json_loads(event.body)
        root = raw.get("id", "unknown")
    except Exception as e:
        root = "unknown"
    subject = root
    return PipelineData(**data, root=root, subject=subject)


@log_action(log_reference=LogReference.COMMON001)
def parse_headers(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    _headers = AbstractHeader(**event.headers).headers
    _raw_connection_metadata = _headers.get(CONNECTION_METADATA, "{}")
    _raw_client_rp_details = _headers.get(CLIENT_RP_DETAILS, "{}")
    connection_metadata = ConnectionMetadata.parse_raw(_raw_connection_metadata)
    client_rp_details = ClientRpDetailsHeader.parse_raw(_raw_client_rp_details)
    add_log_fields(
        connection_metadata=connection_metadata, client_rp_details=client_rp_details
    )  # Might be enough to just mark this log as non-sensitive
    return PipelineData(
        **data,
        ods_code_parts=connection_metadata.ods_code_parts,
        pointer_types=event.requestContext.authorizer.pointer_types,
        nrl_permissions=connection_metadata.nrl_permissions,
        developer_app_id=client_rp_details.developer_app_id,
        developer_app_name=client_rp_details.developer_app_name,
    )


@log_action(log_reference=LogReference.COMMON002)
def parse_path_id(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    """
    Retrieves the {id} from the request path, splits it into different
    representations.
    """
    id = urllib.parse.unquote(event.pathParameters["id"])
    add_log_fields(pointer_id=id)
    pk = convert_document_pointer_id_to_pk(id)
    producer_id, _ = generate_producer_id(id=id, producer_id=None)
    return PipelineData(**data, producer_id=producer_id, id=id, pk=pk)


def make_common_log_action():
    """
    Defines the commonly used request scoped values used in logs.
        * caller - Comes from the developer_app_id value in the nhsd-client-rp-details http header
        * root - Comes from the request path in most instances, or the request body when creating
        * subject - Normally a copy of the root
    """
    return make_scoped_log_action(
        lambda *args, **kwargs: (
            {
                "caller": kwargs.get("data", {}).get("developer_app_id", "unknown"),
                "root": kwargs.get("data", {}).get("root", "unknown"),
                "subject": kwargs.get("data", {}).get("subject", "unknown"),
            }
        )
    )
