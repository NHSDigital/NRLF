import json
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.constants import AUTHORISER_CONTEXT_FIELDS, ApiRequestLevel
from lambda_utils.header_config import AuthHeader, ClientRpDetailsHeader, LoggingHeader
from lambda_utils.logging import log_action
from nrlf.core.authoriser_response import authorisation_denied, authorisation_ok
from nrlf.core.errors import ItemNotFound
from nrlf.core.model import AuthConsumer
from nrlf.core.query import create_read_and_filter_query
from nrlf.core.repository import Repository
from nrlf.core.validators import requesting_application_is_not_authorised
from pydantic import ValidationError


@log_action(narrative="Parsing headers")
def parse_headers(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    raw_client_rp_details = event.headers.get("NHSD-Client-RP-Details", "")
    try:
        logging_headers = LoggingHeader(**event.headers)
        auth_headers = AuthHeader(**event.headers)
        client_rp_details = ClientRpDetailsHeader.parse_raw(raw_client_rp_details)
    except ValidationError as err:
        response = authorisation_denied(
            principal_id="null", resource=data["method_arn"], context={}
        )
        return PipelineData(response=response)

    context = {
        AUTHORISER_CONTEXT_FIELDS.X_CORRELATION_ID: logging_headers.correlation_id,
        AUTHORISER_CONTEXT_FIELDS.NHSD_CORRELATION_ID: logging_headers.nhsd_correlation_id,
        AUTHORISER_CONTEXT_FIELDS.REQUEST_TYPE: ApiRequestLevel.APP_RESTRICTED,
        AUTHORISER_CONTEXT_FIELDS.CLIENT_APP_NAME: client_rp_details.developer_app_name,
        AUTHORISER_CONTEXT_FIELDS.CLIENT_APP_ID: client_rp_details.developer_app_id,
        AUTHORISER_CONTEXT_FIELDS.ORGANISATION_CODE: auth_headers.organisation_code,
    }
    return PipelineData(client_rp_details=client_rp_details, context=context, **data)


@log_action(narrative="Authenticate consumer request")
def authenticate_request(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    response = data.get("response")
    if response:
        return PipelineData(response=response)

    repository: Repository = dependencies["repository"]

    context = data["context"]
    organisation_code = context[AUTHORISER_CONTEXT_FIELDS.ORGANISATION_CODE]
    principle_id = context[AUTHORISER_CONTEXT_FIELDS.NHSD_CORRELATION_ID]
    authentication_query = create_read_and_filter_query(id=organisation_code)

    try:
        authentication_results: AuthConsumer = repository.read(**authentication_query)
    except ItemNotFound:
        response = authorisation_denied(principle_id, data["method_arn"], context)
        return PipelineData(response=response)

    return PipelineData(
        authentication_results=authentication_results,
        **data,
    )


@log_action(narrative="Authorise consumer request")
def authorise_request(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    response = data.get("response")
    if response:
        return PipelineData(response=response)

    authentication_results = data["authentication_results"]
    client_rp_details: ClientRpDetailsHeader = data["client_rp_details"]
    context = data["context"]
    principle_id = context[AUTHORISER_CONTEXT_FIELDS.NHSD_CORRELATION_ID]

    if requesting_application_is_not_authorised(
        client_rp_details.developer_app_id,
        authentication_results.application_id.__root__,
    ):
        response = authorisation_denied(principle_id, data["method_arn"], context)
        return PipelineData(response=response)

    return PipelineData(**data)


@log_action(narrative="Authorising consumer request")
def authorise(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    response = data.get("response")
    if response:
        return PipelineData(response)

    authentication_results = data["authentication_results"]
    context = data["context"]
    context["document_types"] = json.dumps(
        authentication_results.document_types.__root__
    )

    principle_id = context[AUTHORISER_CONTEXT_FIELDS.NHSD_CORRELATION_ID]

    response = authorisation_ok(principle_id, data["method_arn"], context)
    return PipelineData(response)


steps = [
    parse_headers,
    authenticate_request,
    authorise_request,
    authorise,
]
