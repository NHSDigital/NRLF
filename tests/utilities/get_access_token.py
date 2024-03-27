import base64
import json
from time import time
from typing import Literal
from uuid import uuid4

import boto3
import fire
import jwt
import requests

_DEFAULT_APP_DEV = "4e41d2d9-3ef6-48dc-8406-5faba77ffd83"
_DEFAULT_APP_PROD = "7a4ad8c7-3927-4259-af7b-ac9d305a86ad"
_DEFAULT_APP_FOR_APIGEE_ENV = {
    "internal-dev": _DEFAULT_APP_DEV,
    "internal-dev-sandbox": _DEFAULT_APP_DEV,
    "internal-qa": _DEFAULT_APP_DEV,
    "internal-qa-sandbox": _DEFAULT_APP_DEV,
    "int": _DEFAULT_APP_PROD,
    "int-sandbox": _DEFAULT_APP_PROD,
    "prod": _DEFAULT_APP_PROD,
}

_NRL_SYNC_APP_DEV = "94492ef7-40a5-47bb-a18b-b9023bd4ec9a"
_NRL_SYNC_APP_PROD = "f9822096-11ec-479f-8d95-fcc8dd22048d"
_NRL_SYNC_APP_FOR_APIGEE_ENV = {
    "internal-dev": _NRL_SYNC_APP_DEV,
    "internal-qa": _NRL_SYNC_APP_DEV,
    "int": _NRL_SYNC_APP_PROD,
    "prod": _NRL_SYNC_APP_PROD,
}

AWS_ACCOUNT_FOR_ENV = {
    "dev": "dev",
    "int": "test",
    "ref": "test",
    "prod": "prod",
}
APIGEE_ENV_FOR_ENV = {
    "dev": "internal-dev",
    "dev-sandbox": "internal-dev-sandbox",
    "ref": "internal-qa",
    "ref-sandbox": "internal-qa-sandbox",
    "int": "int",
    "int-sandbox": "sandbox",
    "prod": "prod",
}
APP_FOR_ALIAS = {
    "default": _DEFAULT_APP_FOR_APIGEE_ENV,
    "nrl_sync": _NRL_SYNC_APP_FOR_APIGEE_ENV,
}


def get_app_details(env: str, app_alias: str):
    if env not in AWS_ACCOUNT_FOR_ENV:
        raise ValueError(f"Invalid environment: {env}")

    account_name = AWS_ACCOUNT_FOR_ENV[env]
    apigee_env = APIGEE_ENV_FOR_ENV[env]
    app_id = APP_FOR_ALIAS[app_alias][apigee_env]

    return account_name, app_id


def get_target_account_id(account: str):
    secretsmanager = boto3.client("secretsmanager", region_name="eu-west-2")
    secret_id = f"nhsd-nrlf--mgmt--{account}-account-id"
    result = secretsmanager.get_secret_value(SecretId=secret_id)
    return result["SecretString"]


def get_boto_session_for_account(account_id: str):
    sts = boto3.client("sts", region_name="eu-west-2")
    result = sts.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/terraform",
        RoleSessionName="get-account-id",
        DurationSeconds=900,
    )
    credentials = result["Credentials"]

    return boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )


def get_app_secrets(account_name: str, env: str, app_id: str):
    account_id = get_target_account_id(account_name)
    session = get_boto_session_for_account(account_id)
    secretsmanager = session.client("secretsmanager", region_name="eu-west-2")
    secret_id = f"nhsd-nrlf--{account_name}--{env}--apigee-app-token-info--{app_id}"
    result = secretsmanager.get_secret_value(SecretId=secret_id)
    secret = json.loads(result["SecretString"])
    secret["private_key"] = base64.b64decode(secret["private_key"])
    return secret


def generate_client_assertion(app_secrets: dict):
    return jwt.encode(
        {
            "iss": app_secrets["api_key"],
            "sub": app_secrets["api_key"],
            "aud": app_secrets["oauth_url"],
            "jti": str(uuid4()),
            "exp": time() + 300,
        },
        app_secrets["private_key"],
        algorithm="RS512",
        headers={"kid": app_secrets["kid"]},
    )


def make_token_request(app_secrets: dict, token: str):
    response = requests.post(
        url=app_secrets["oauth_url"],
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": token,
        },
    )
    return response.json()


def main(env: str, app_alias: Literal["default", "nrl_sync"] = "default"):

    account_name, app_id = get_app_details(env, app_alias)

    print(  # noqa: T201
        f"Requesting access token for {env} environment (App ID '{app_id}')"
    )

    app_secrets = get_app_secrets(account_name, env, app_id)
    jwt_token = generate_client_assertion(app_secrets)

    response = make_token_request(app_secrets, jwt_token)

    access_token = response["access_token"]
    print(f"Access Token: {access_token}")  # noqa: T201


if __name__ == "__main__":
    fire.Fire(main)
