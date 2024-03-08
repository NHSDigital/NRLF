from datetime import datetime
from functools import cache

import boto3
import botocore.session

from helpers.log import log
from helpers.terraform import get_terraform_json

DEFAULT_WORKSPACE = "dev"

# Map an environment to an AWS Account
AWS_ACCOUNT_FOR_ENV = {
    DEFAULT_WORKSPACE: "dev",
    "int": "test",
    "ref": "test",
    "prod": "prod",
}


@log("Got account id '{__result__}' from {env}")
def aws_account_id_from_profile(env: str):
    account = AWS_ACCOUNT_FOR_ENV[env]
    profile_names = [f"nhsd-nrlf-{account}-admin", f"nhsd-nrlf-{account}"]

    session = botocore.session.Session()
    profiles = session.full_config["profiles"]

    for name in profile_names:
        profile = profiles.get(name, {})
        account_id = profile.get("aws_account_id") or profile.get("sso_account_id")
        if account_id:
            return account_id

    raise Exception("No valid profile found")


def _get_access_token(account_id: str = None):
    if not account_id:
        account_id = get_terraform_json()["assume_account_id"]["value"]
    sts_client = boto3.client("sts")
    current_time = datetime.utcnow().timestamp()
    response = sts_client.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/terraform",
        RoleSessionName=f"nrlf-test-{current_time}",
    )

    access_key_id = response["Credentials"]["AccessKeyId"]
    secret_access_key = response["Credentials"]["SecretAccessKey"]
    session_token = response["Credentials"]["SessionToken"]
    return access_key_id, secret_access_key, session_token


@cache
def new_aws_session(account_id: str = None) -> boto3.Session:
    access_key_id, secret_access_key, session_token = _get_access_token(
        account_id=account_id
    )

    return boto3.Session(
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        aws_session_token=session_token,
    )


def new_session_from_env(env: str) -> boto3.Session:
    account_id = aws_account_id_from_profile(env=env)
    return new_aws_session(account_id=account_id)
