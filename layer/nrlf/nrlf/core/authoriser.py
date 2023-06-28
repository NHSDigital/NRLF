import json
from enum import Enum
from http import HTTPStatus
from logging import Logger
from typing import Any

from lambda_pipeline.types import FrozenDict, LambdaContext, PipelineData
from lambda_utils.header_config import (
    AbstractHeader,
    ClientRpDetailsHeader,
    ConnectionMetadata,
)
from lambda_utils.logging import log_action
from lambda_utils.logging_utils import generate_transaction_id
from lambda_utils.pipeline import (
    APIGatewayProxyEventModel,
    _execute_steps,
    _setup_logger,
)
from pydantic import BaseModel, ValidationError

from nrlf.core.constants import CLIENT_RP_DETAILS, CONNECTION_METADATA
from nrlf.core.types import S3Client
from nrlf.core.validators import json_loads


class LogReference(Enum):
    AUTHORISER001 = "Parsing headers"
    AUTHORISER002 = "Parsing pointer types"
    AUTHORISER003 = "Reading pointer types from S3"
    AUTHORISER004 = "Validating pointer types"
    AUTHORISER005 = "Render authorisation response"
    AUTHORISER006 = "Parsing Client RP Details"


class _PermissionsLookupError(Exception):
    pass


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
    AUTH_STORE: str


def build_persistent_dependencies(
    config: Config, s3_client: S3Client
) -> dict[str, any]:
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
        "permissions_lookup_bucket": config.AUTH_STORE,
        "s3_client": s3_client,
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


@log_action(log_reference=LogReference.AUTHORISER006, log_result=True)
def _parse_client_rp_details(raw_client_rp_details: dict):
    return ClientRpDetailsHeader.parse_raw(raw_client_rp_details)


@log_action(log_reference=LogReference.AUTHORISER003, log_result=True)
def _parse_list_from_s3(s3_client: S3Client, bucket: str, key: str) -> list:
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
    except s3_client.exceptions.NoSuchKey:
        raise _PermissionsLookupError(
            "No permissions were found for the provided credentials, contact onboarding team."
        )

    try:
        items = json_loads(response["Body"].read())
    except json.JSONDecodeError:
        raise _PermissionsLookupError("Malformed permissions, contact onboarding team.")

    return items


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
        client_rp_details = _parse_client_rp_details(
            raw_client_rp_details=_raw_client_rp_details, logger=logger
        )
    except ValidationError:
        return PipelineData(
            error="There was an issue parsing the client rp details, contact onboarding team",
            **data,
        )

    return PipelineData(
        connection_metadata=connection_metadata,
        client_rp_details=client_rp_details,
        **data,
    )


@log_action(log_reference=LogReference.AUTHORISER002)
def retrieve_pointer_types(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    if data.get("error"):
        return PipelineData(**data)

    client_rp_details: ClientRpDetailsHeader = data["client_rp_details"]
    connection_metadata: ConnectionMetadata = data["connection_metadata"]

    pointer_types = connection_metadata.pointer_types
    if connection_metadata.enable_authorization_lookup:
        ods_code = ".".join(connection_metadata.ods_code_parts)
        try:
            pointer_types = _parse_list_from_s3(
                s3_client=dependencies["s3_client"],
                bucket=dependencies["permissions_lookup_bucket"],
                key=f"{client_rp_details.developer_app_id}/{ods_code}.json",
                logger=logger,
            )
        except _PermissionsLookupError as exc:
            return PipelineData(error=str(exc), **data)

    return PipelineData(pointer_types=pointer_types, **data)


@log_action(log_reference=LogReference.AUTHORISER004)
def validate_pointer_types(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    if data.get("error"):
        return PipelineData(**data)

    if data.get("pointer_types") == []:
        return PipelineData(error="No pointer types have been provided", **data)
    return PipelineData(**data)


@log_action(log_reference=LogReference.AUTHORISER005)
def generate_response(
    data: PipelineData,
    context: LambdaContext,
    event: APIGatewayProxyEventModel,
    dependencies: FrozenDict[str, Any],
    logger: Logger,
) -> PipelineData:
    error = data.get("error")
    pointer_types = data.get("pointer_types")
    policy = _create_policy(
        principal_id=logger.transaction_id,
        resource=data["method_arn"],
        effect="Deny" if error else "Allow",
        context=(
            {"error": error} if error else {"pointer-types": json.dumps(pointer_types)}
        ),
    )
    return PipelineData(policy)


steps = [
    parse_headers,
    retrieve_pointer_types,
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
