from datetime import datetime
from functools import cache

import boto3

from helpers.terraform import get_terraform_json


def _get_access_token():
    account_id = get_terraform_json()["assume_account_id"]["value"]
    sts_client = boto3.client("sts")
    current_time = datetime.utcnow().timestamp()
    response = sts_client.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/terraform",
        RoleSessionName=f"nrlf-feature-test-{current_time}",
    )

    access_key_id = response["Credentials"]["AccessKeyId"]
    secret_access_key = response["Credentials"]["SecretAccessKey"]
    session_token = response["Credentials"]["SessionToken"]
    return access_key_id, secret_access_key, session_token


@cache
def new_aws_session() -> boto3.Session:
    access_key_id, secret_access_key, session_token = _get_access_token()

    return boto3.Session(
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        aws_session_token=session_token,
    )
