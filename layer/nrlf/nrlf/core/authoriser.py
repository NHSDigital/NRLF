import json
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.constants import CLIENT_RP_DETAILS, NULL, ApiRequestLevel
from lambda_utils.header_config import AuthHeader, ClientRpDetailsHeader, LoggingHeader
from lambda_utils.logging import log_action
from nrlf.core.errors import ItemNotFound
from nrlf.core.model import AuthBase, AuthoriserContext
from nrlf.core.query import create_read_and_filter_query
from nrlf.core.repository import Repository
from nrlf.core.validators import requesting_application_is_not_authorised
from pydantic import ValidationError


def _authorisation_ok(principal_id, resource, context):
    return _create_policy(principal_id, resource, "Allow", context)


def _authorisation_denied(principal_id, resource, context):
    return _create_policy(principal_id, resource, "Deny", context)


def _create_policy(principal_id, resource, effect, context):
    return {
        "principalId": principal_id,
        "context": context,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "execute-api:Invoke", "Effect": effect, "Resource": resource}
            ],
        },
    }


@log_action(narrative="Parsing headers")
def parse_headers(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    raw_client_rp_details = event.headers.get(CLIENT_RP_DETAILS, "")
    try:
        logging_headers = LoggingHeader(**event.headers)
        auth_headers = AuthHeader(**event.headers)
        client_rp_details = ClientRpDetailsHeader.parse_raw(raw_client_rp_details)
    except ValidationError:
        response = _authorisation_denied(
            principal_id=NULL, resource=data["method_arn"], context={}
        )
        return PipelineData(response=response)

    deny_context = AuthoriserContext(
        correlation_id=logging_headers.correlation_id,
        nhsd_correlation_id=logging_headers.nhsd_correlation_id,
        request_type=ApiRequestLevel.APP_RESTRICTED,
        client_app_name=client_rp_details.developer_app_name,
        client_app_id=client_rp_details.developer_app_id,
        organisation_code=auth_headers.organisation_code,
    )

    deny_response = _authorisation_denied(
        principal_id=logging_headers.correlation_id,
        resource=data["method_arn"],
        context=deny_context.dict(by_alias=True, exclude_none=True),
    )

    return PipelineData(
        client_rp_details=client_rp_details,
        logging_headers=logging_headers,
        auth_headers=auth_headers,
        deny_response=deny_response,
        **data,
    )


@log_action(narrative="Authenticate request")
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

    org_code = data["auth_headers"].organisation_code
    authentication_query = create_read_and_filter_query(id=org_code)
    repository: Repository = dependencies["repository"]
    try:
        authentication_results: AuthBase = repository.read(**authentication_query)
    except ItemNotFound:
        return PipelineData(response=data["deny_response"])

    return PipelineData(
        authentication_results=authentication_results,
        **data,
    )


@log_action(narrative="Authorise request")
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

    if requesting_application_is_not_authorised(
        data["client_rp_details"].developer_app_id,
        data["authentication_results"].application_id.__root__,
    ):
        return PipelineData(response=data["deny_response"])
    return PipelineData(**data)


@log_action(narrative="Generate 'Allow' response")
def generate_allow_response(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    response = data.get("response")
    if response:
        return PipelineData(response)

    authoriser_context = AuthoriserContext(
        correlation_id=data["logging_headers"].correlation_id,
        nhsd_correlation_id=data["logging_headers"].nhsd_correlation_id,
        request_type=ApiRequestLevel.APP_RESTRICTED,
        client_app_name=data["client_rp_details"].developer_app_name,
        client_app_id=data["client_rp_details"].developer_app_id,
        organisation_code=data["auth_headers"].organisation_code,
        pointer_types=json.dumps(data["authentication_results"].pointer_types.__root__),
    )

    response = _authorisation_ok(
        principal_id=authoriser_context.correlation_id,
        resource=data["method_arn"],
        context=authoriser_context.dict(by_alias=True),
    )
    return PipelineData(response)


steps = [
    parse_headers,
    authenticate_request,
    authorise_request,
    generate_allow_response,
]
