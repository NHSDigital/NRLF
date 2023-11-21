from datetime import datetime
from pathlib import Path

import boto3
import pytest

from nrlf.core.validators import json_load

LIMIT = 100
ENABLED = "ENABLED"
PATH_TO_HERE = Path(__file__).parent
PATH_TO_OUTPUT = PATH_TO_HERE.parent / "output.json"
ROLE_ARN = "arn:aws:iam::{account_id}:role/terraform".format
ROLE_SESSION_NAME = "integration-test-{timestamp}".format
TABLE_NAME_SUFFIXES = ["document-pointer"]


def _get_access_token(account_id: str) -> dict[str:str]:
    sts_client = boto3.client("sts")
    timestamp = datetime.utcnow().timestamp()
    response = sts_client.assume_role(
        RoleArn=ROLE_ARN(account_id=account_id),
        RoleSessionName=ROLE_SESSION_NAME(timestamp=timestamp),
    )
    credentials = response["Credentials"]
    return {
        "aws_access_key_id": credentials["AccessKeyId"],
        "aws_secret_access_key": credentials["SecretAccessKey"],
        "aws_session_token": credentials["SessionToken"],
    }


def _get_aws_account_id():
    with open(PATH_TO_OUTPUT) as f:
        tf_output = json_load(f)
    return tf_output["assume_account_id"]["value"]


@pytest.fixture(scope="session")
def aws_session() -> boto3.Session:
    aws_account_id = _get_aws_account_id()
    credentials = _get_access_token(aws_account_id)
    yield boto3.Session(**credentials)


@pytest.fixture
def workspace():
    with open(PATH_TO_OUTPUT) as f:
        tf_output = json_load(f)
    return tf_output["workspace"]["value"]


@pytest.fixture(scope="session")
def dynamodb(aws_session):
    yield aws_session.client("dynamodb")


@pytest.fixture
def table_names(dynamodb, workspace):
    response = dynamodb.list_tables(Limit=LIMIT)
    table_names = [
        table_name
        for table_name in response["TableNames"]
        if workspace in table_name
        and any(table_name.endswith(suffix) for suffix in TABLE_NAME_SUFFIXES)
    ]
    return table_names


@pytest.mark.integration
def test_table_names(table_names):
    assert table_names, "No dynamodb tables found"
    if len(table_names) == LIMIT:
        raise ValueError(
            f"boto3.client('dynamodb').list_tables: Limit argument not set high enough"
        )


@pytest.mark.integration
def test_dynamodb_encryption(dynamodb, table_names):
    for table_name in table_names:
        response = dynamodb.describe_table(TableName=table_name)
        assert response["Table"]["SSEDescription"]["Status"] == ENABLED


@pytest.mark.integration
def test_dynamodb_deletion_protection(dynamodb, table_names):
    for table_name in table_names:
        response = dynamodb.describe_table(TableName=table_name)
        if "--prod--" in table_name or "--uat--" in table_name:
            assert response["Table"]["DeletionProtectionEnabled"] == True
        else:
            assert response["Table"]["DeletionProtectionEnabled"] == False
