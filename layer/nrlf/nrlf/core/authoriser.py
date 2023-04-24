from enum import Enum
from http import HTTPStatus
from logging import Logger
from typing import Any

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.constants import CLIENT_RP_DETAILS, CONNECTION_METADATA
from lambda_utils.header_config import (
    AbstractHeader,
    ClientRpDetailsHeader,
    ConnectionMetadata,
)
from lambda_utils.logging import log_action
from lambda_utils.logging_utils import generate_transaction_id
from lambda_utils.pipeline import _execute_steps, _setup_logger
from pydantic import BaseModel, ValidationError


class LogReference(Enum):
    AUTHORISER001 = "Parsing headers"
    AUTHORISER002 = "Validating pointer types"
    AUTHORISER003 = "Render authorisation response"
    AUTHORISER004 = "Parsing Client RP Details"


class Config(BaseModel):
    """
    The Config class defines all the Environment Variables that are needed for
    the business logic to execute successfully.
    All Environment Variables are validated using pydantic, and will result in
    a 500 Internal Server Error if validation fails.

    To add a new Environment Variable simply a new pydantic compatible
    definition below, and pydantic should allow for even complex validation
    logic to be supported.
    """

    AWS_REGION: str
    PREFIX: str
    ENVIRONMENT: str
    SPLUNK_INDEX: str
    SOURCE: str


def build_persistent_dependencies(config: Config) -> dict[str, any]:
    """
    AWS Lambdas may be re-used, rather than spinning up a new instance each
    time.  Doing this we can take advantage of state that persists between
    executions.  Any dependencies returned by this function will persist
    between executions and can therefore lead to performance gains.
    This function will be called ONCE in the lambdas lifecycle, which may or
    may not be each execution, depending on how busy the API is.
    These dependencies will be passed through to your `handle` function below.
    """
    return {
        "environment": config.ENVIRONMENT,
        "splunk_index": config.SPLUNK_INDEX,
        "source": config.SOURCE,
    }


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


@log_action(log_reference=LogReference.AUTHORISER004, log_result=True)
def _parse_client_rp_details(raw_client_rp_details: dict):
    return ClientRpDetailsHeader.parse_raw(raw_client_rp_details)


@log_action(log_reference=LogReference.AUTHORISER001)
def parse_headers(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    _headers = AbstractHeader(**event.headers).headers
    _raw_client_rp_details = _headers.get(CLIENT_RP_DETAILS, "{}")
    _raw_connection_metadata = _headers.get(CONNECTION_METADATA, "{}")
    try:
        connection_metadata = ConnectionMetadata.parse_raw(_raw_connection_metadata)
    except ValidationError:
        return PipelineData(
            error="There was an issue parsing the connection metadata, contact onboarding team",
            **data,
        )

    try:
        _parse_client_rp_details(
            raw_client_rp_details=_raw_client_rp_details, logger=logger
        )
    except ValidationError:
        return PipelineData(
            error="There was an issue parsing the client rp details, contact onboarding team",
            **data,
        )

    return PipelineData(pointer_types=connection_metadata.pointer_types, **data)


@log_action(log_reference=LogReference.AUTHORISER002)
def validate_pointer_types(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    if data.get("pointer_types") == []:
        return PipelineData(
            error={"message": "No pointer types have been provided"}, **data
        )
    return PipelineData(**data)


@log_action(log_reference=LogReference.AUTHORISER003)
def generate_response(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    error = data.get("error")
    policy = _create_policy(
        principal_id=logger.transaction_id,
        resource=data["method_arn"],
        effect="Deny" if error else "Allow",
        context={"error": error["message"]} if error else {},
    )
    return PipelineData(policy)


steps = [
    parse_headers,
    validate_pointer_types,
    generate_response,
]


def _function_handler(
    fn, transaction_id: str, status_code_ok: HTTPStatus, method_arn: str, args, kwargs
) -> tuple[HTTPStatus, any]:
    try:
        status_code, result = status_code_ok, fn(*args, **kwargs)
    except Exception:
        status_code = None
        result = _create_policy(
            principal_id=transaction_id,
            resource=method_arn,
            effect="Deny",
            context={"error": HTTPStatus.INTERNAL_SERVER_ERROR.phrase},
        )
    return status_code, result


def execute_steps(
    index_path: str,
    event: dict,
    context: LambdaContext,
    initial_pipeline_data={},
    **dependencies,
) -> tuple[HTTPStatus, dict]:
    """
    Executes the handler and wraps it in exception handling
    """
    if context is None:
        context = LambdaContext()

    # This field isnt in the event for authoriser requests for some reason
    # adding it here to pass pydantic validation later
    event["isBase64Encoded"] = False
    transaction_id = generate_transaction_id()
    method_arn = event["methodArn"]

    status_code, response = _function_handler(
        _setup_logger,
        transaction_id=transaction_id,
        status_code_ok=HTTPStatus.OK,
        method_arn=method_arn,
        args=(index_path, transaction_id, event),
        kwargs=dependencies,
    )

    if status_code is not HTTPStatus.OK:
        return status_code, response
    logger = response

    return _function_handler(
        _execute_steps,
        transaction_id=transaction_id,
        status_code_ok=HTTPStatus.OK,
        method_arn=method_arn,
        args=(steps, event, context),
        kwargs={
            "logger": logger,
            "dependencies": dependencies,
            "initial_pipeline_data": {"method_arn": method_arn},
        },
    )
