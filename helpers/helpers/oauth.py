import base64
import time
from functools import cache
from typing import Literal
from uuid import uuid4

import boto3
import fire
import jwt
import requests

from helpers.log import log
from nrlf.core.validators import json_loads

EXPIRATION_TIME_SECONDS = 30

AWS_ACCOUNT_FOR_ENV = {
    "dev": "dev",
    "int": "test",
    "ref": "test",
    "prod": "prod",
}

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

DEFAULT_APP_ALIAS = "default"
NRL_SYNC_APP_ALIAS = "nrl_sync"
APP_FOR_ALIAS = {
    DEFAULT_APP_ALIAS: _DEFAULT_APP_FOR_APIGEE_ENV,
    NRL_SYNC_APP_ALIAS: _NRL_SYNC_APP_FOR_APIGEE_ENV,
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

secrets_client = boto3.client("secretsmanager", region_name="eu-west-2")


@log("Generating jwt")
def _generate_jwt(
    jwt_private_key: str,
    oauth_url: str,
    api_key: str,
    uuid: str,
    expires: float,
    kid: str,
):
    payload = {
        "iss": api_key,
        "sub": api_key,
        "aud": oauth_url,
        "jti": uuid,
        "exp": expires,
    }
    return jwt.encode(payload, jwt_private_key, algorithm="RS512", headers={"kid": kid})


@log("Requesting OAuth token from '{oauth_url}'")
def _oauth_access_token(jwt_token: str, oauth_url: str):
    response = requests.post(
        url=oauth_url,
        headers={"content-type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": jwt_token,
        },
    )
    response.raise_for_status()
    return json_loads(response.text)["access_token"]


@log("Reading secret '{secret_id}'")
def _aws_read_apigee_app_secrets(secret_id: str):
    response = secrets_client.get_secret_value(SecretId=secret_id)
    secret = json_loads(response["SecretString"])

    api_key = secret["api_key"]
    oauth_url = secret["oauth_url"]
    kid = secret["kid"]
    private_key = base64.b64decode(secret["private_key"]).decode("utf-8")
    # Check other required fields are present
    for field in ["apigee_url", "public_key"]:
        secret[field]  # Will raise KeyError if missing

    return api_key, oauth_url, kid, private_key


@log("Got OAuth token: {__result__}")
@cache
def get_oauth_token(account: str, env: str, app_id: str):
    secret_id = f"nhsd-nrlf--{account}--{env}--apigee-app-token-info--{app_id}"
    try:
        api_key, oauth_url, kid, jwt_private_key = _aws_read_apigee_app_secrets(
            secret_id=secret_id
        )
    except Exception as e:
        raise Exception(f"Cannot find secret {secret_id}") from e

    jwt_token = _generate_jwt(
        jwt_private_key=jwt_private_key,
        oauth_url=oauth_url,
        api_key=api_key,
        uuid=f"correlation-id-{uuid4()}",
        expires=time.time() + EXPIRATION_TIME_SECONDS,
        kid=kid,
    )

    return _oauth_access_token(jwt_token=jwt_token, oauth_url=oauth_url)


def token(env: str, app_alias: Literal["default", "nrl_sync"] = DEFAULT_APP_ALIAS):
    account = AWS_ACCOUNT_FOR_ENV[env]
    apigee_env = APIGEE_ENV_FOR_ENV[env]
    app_id = APP_FOR_ALIAS[app_alias][apigee_env]

    return get_oauth_token(env=env, account=account, app_id=app_id)


if __name__ == "__main__":
    fire.Fire(token)
