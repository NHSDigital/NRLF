import json
import os
from copy import copy, deepcopy
from functools import cache
from importlib import import_module
from pathlib import Path

import boto3
import yaml
from behave.model import Table
from behave.runner import Context
from lambda_utils.header_config import LoggingHeader
from lambda_utils.logging_utils import generate_transaction_id

from feature_tests.common.constants import (
    ACTION_ALIASES,
    ALLOWED_CONSUMER_ORG_IDS,
    ALLOWED_CONSUMERS,
    ALLOWED_PRODUCER_ORG_IDS,
    ALLOWED_PRODUCERS,
    AUTH_STORE,
    Action,
    ActorType,
    TestMode,
)
from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json
from nrlf.core.types import DynamoDbClient, S3Client

RELATES_TO = "relatesTo"
TARGET = "target"

PATH_TO_HERE = Path(__file__).parent


def _json_escape(value: str) -> str:
    return value.replace('"', '\\"')


def render_regular_properties(raw: str, table: Table):
    rendered = copy(raw)
    if table is None:
        table = []
    for row in table:
        if row["property"] == TARGET:
            continue
        rendered = rendered.replace(f'${row["property"]}', _json_escape(row["value"]))
    return rendered


def render_document_reference_properties(
    document_reference_json: dict, table: Table
) -> str:
    (_relatesTo,) = document_reference_json.pop(RELATES_TO, [None])
    relatesTo_collection = []
    if _relatesTo:
        for row in table:
            if row["property"] != TARGET:
                continue
            relatesTo = deepcopy(_relatesTo)
            if relatesTo["target"].get("identifier"):
                relatesTo["target"]["identifier"]["value"] = row["value"]
            relatesTo_collection.append(relatesTo)
    if relatesTo_collection:  # Empty fields aren't valid FHIR
        document_reference_json[RELATES_TO] = relatesTo_collection
    return json.dumps(document_reference_json)


def logging_headers(scenario_name) -> dict:
    uuid = generate_transaction_id()
    return LoggingHeader(
        **{
            "x-correlation-id": f"{scenario_name}|{uuid}",
            "nhsd-correlation-id": f"{scenario_name}|{uuid}",
            "x-request-id": uuid,
        }
    ).dict(by_alias=True)


def _get_boto3_client(client_name: str, test_mode: TestMode):
    session = boto3 if test_mode is TestMode.LOCAL_TEST else new_aws_session()
    return session.client(client_name)


def get_dynamodb_client(test_mode: TestMode) -> DynamoDbClient:
    return _get_boto3_client(client_name="dynamodb", test_mode=test_mode)


def get_s3_client(test_mode: TestMode) -> S3Client:
    return _get_boto3_client(client_name="s3", test_mode=test_mode)


def get_lambda_client(test_mode: TestMode) -> any:
    return _get_boto3_client(client_name="lambda", test_mode=test_mode)


def get_test_mode(context: Context) -> TestMode:
    return (
        TestMode.INTEGRATION_TEST
        if context.config.userdata.get("integration_test", "false") == "true"
        else TestMode.LOCAL_TEST
    )


def get_environment_prefix(test_mode: TestMode) -> str:
    return (
        ""
        if test_mode is TestMode.LOCAL_TEST
        else f'{get_terraform_json()["prefix"]["value"]}--'
    )


def get_auth_store(test_mode: TestMode) -> str:
    return (
        AUTH_STORE
        if test_mode is TestMode.LOCAL_TEST
        else get_terraform_json()["auth_store"]["value"]
    )


def get_endpoint(test_mode: TestMode, actor_type: ActorType) -> str:
    return (
        ""
        if test_mode is TestMode.LOCAL_TEST
        else get_terraform_json()["api_base_urls"]["value"][actor_type.name.lower()]
    )


def get_tls_ma_files(test_mode: TestMode) -> str:
    """
    The mTLS certs are stored in /nrlf/truststore/client

    Before running the tests you must download them

    nrlf truststore pull-client <account>
    """
    if test_mode == TestMode.LOCAL_TEST:
        return None
    account_name = get_terraform_json()["account_name"]["value"]
    dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "../../truststore/client")
    )
    cert = os.path.join(dir, f"{account_name}.crt")
    key = os.path.join(dir, f"{account_name}.key")
    if not (os.path.exists(cert) and os.path.exists(key)):
        raise Exception(
            f"mTLS certificates not present.\ntry: nrlf truststore pull-client {account_name}"
        )
    return (cert, key)


def get_lambda_arn(test_mode: TestMode, actor_type: ActorType) -> str:
    return (
        ""
        if test_mode is TestMode.LOCAL_TEST
        else get_terraform_json()["authoriser_lambda_function_names"]["value"][
            actor_type.name.lower()
        ]
    )


@cache
def get_api_definitions_from_swagger(actor_type: ActorType):
    path_to_repo_base = PATH_TO_HERE.parent.parent.resolve()
    path_to_swagger = (
        path_to_repo_base / "api" / actor_type.name.lower() / "swagger.yaml"
    )
    with open(path_to_swagger) as f:
        swagger = yaml.load(f, Loader=yaml.FullLoader)
    paths = swagger["paths"]
    api_definitions = {}
    for method_slug, method_collection in paths.items():
        for request_method, api_definition in method_collection.items():
            operation_id = api_definition["operationId"]
            action = operation_id.replace("DocumentReference", "")
            api_definitions[action] = {
                "method_slug": method_slug,
                "request_method": request_method,
            }
    return api_definitions


def get_lambda_handler(actor_type: ActorType, action: Action, suffix: str = ""):
    actor_type = actor_type.name.lower()
    index = import_module(f"api.{actor_type}.{action.name}{suffix}.index")
    return index.handler


def table_as_dict(table: Table) -> dict:
    return {row["property"]: row["value"] for row in table if row["value"] != "null"}


def get_org_id(org_id: str, actor_type: ActorType) -> str:
    allowed_org_ids = (
        ALLOWED_CONSUMER_ORG_IDS
        if actor_type is ActorType.Consumer
        else ALLOWED_PRODUCER_ORG_IDS
    )
    if org_id not in allowed_org_ids:
        raise ValueError(
            f"Organisation ID {org_id} of type {actor_type.name} must be one of {allowed_org_ids}"
        )
    return org_id


def get_actor(actor: str, actor_type: ActorType) -> str:
    allowed_actors = (
        ALLOWED_CONSUMERS if actor_type is ActorType.Consumer else ALLOWED_PRODUCERS
    )
    if actor not in allowed_actors:
        raise ValueError(
            f"Actor name {actor} of type {actor_type.name} must be one of {allowed_actors}"
        )
    return actor


def get_action(action_name: str) -> Action:
    action_name = ACTION_ALIASES.get(action_name) or action_name
    action = Action._member_map_.get(action_name)
    if not action:
        raise ValueError(
            f"Action name {action_name} must be one of {Action._member_names_} or {list(ACTION_ALIASES.keys())}"
        )
    return action


def get_actor_type(actor_type_name: str) -> Action:
    actor_type = ActorType._member_map_.get(actor_type_name)
    if not actor_type:
        raise ValueError(
            f"ActorType name {actor_type_name} must be one of {ActorType._member_names_}"
        )
    return actor_type
