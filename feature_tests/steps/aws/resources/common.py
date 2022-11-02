import json
from datetime import datetime
from pathlib import Path

import boto3

terraform_output_json_path = str(
    Path(__file__).parent.parent.parent.parent.parent
    / "terraform"
    / "infrastructure"
    / "output.json"
)


def get_terraform_json() -> dict:
    with open(terraform_output_json_path, "r") as f:
        return json.loads(f.read())


def get_access_token():
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


def new_aws_session() -> boto3.Session:
    access_key_id, secret_access_key, session_token = get_access_token()

    return boto3.Session(
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        aws_session_token=session_token,
    )
