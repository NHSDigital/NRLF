import json
from typing import Dict, List

import boto3
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    APIGatewayAuthorizerRequestEvent,
    APIGatewayAuthorizerResponse,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

from nrlf.core.config import AuthorizerConfig
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import logger
from nrlf.core.request import parse_headers

CONFIG = AuthorizerConfig()


def get_pointer_types(headers: Dict[str, str]) -> List[str]:
    connection_metadata = parse_headers(headers)
    logger.debug("Connection metadata", connection_metadata=connection_metadata)

    if not connection_metadata.enable_authorization_lookup:
        logger.info("Authorization lookup is disabled", headers=headers)
        return connection_metadata.pointer_types

    ods_code = ".".join(connection_metadata.ods_code_parts)
    app_id = connection_metadata.client_rp_details.developer_app_id
    key = f"{app_id}/{ods_code}.json"
    logger.debug("Getting pointer types", key=key)

    s3_client = boto3.client("s3")

    try:
        response = s3_client.get_object(Bucket=CONFIG.AUTH_STORE, Key=key)
        pointer_types = json.loads(response["Body"].read())
        logger.debug("Pointer types", pointer_types=pointer_types)
        return pointer_types

    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "NoSuchKey":
            logger.info("No pointer types found", headers=headers)
            return []

        raise exc

    except Exception as exc:
        logger.exception("Failed to get pointer types", headers=headers, error=str(exc))
        raise exc


@event_source(data_class=APIGatewayAuthorizerRequestEvent)
def handler(event: APIGatewayAuthorizerRequestEvent, context: LambdaContext):
    """"""
    try:
        pointer_types = get_pointer_types(event.headers)

    except OperationOutcomeError as error:
        logger.error("Failed to get pointer types", headers=event.headers, error=error)
        pointer_types = []

    arn = event.parsed_arn
    policy = APIGatewayAuthorizerResponse(
        principal_id=logger.get_correlation_id() or "",
        region=arn.region,
        context={"pointer_types": json.dumps(pointer_types)},
        aws_account_id=arn.aws_account_id,
        api_id=arn.api_id,
        stage=arn.stage,
    )

    if pointer_types == []:
        policy.deny_route(http_method=arn.http_method, resource=arn.resource)
        policy.context = {"error": "No pointer types found"}
        logger.info("No pointer types found", headers=event.headers)

    else:
        policy.allow_route(http_method=arn.http_method, resource=arn.resource)

    response = policy.asdict()
    logger.info("Authorizer response", response=response)

    return response
