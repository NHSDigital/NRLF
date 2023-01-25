import base64
import json
import os
import sys
import time
import urllib.parse
from datetime import datetime
from functools import cache
from uuid import uuid4

import boto3
import botocore.session
import jwt
import pytest
import requests
from fire import Fire

from helpers.terraform import get_terraform_json

DEFAULT_WORKSPACE = "dev"

# Map an environment to an AWS Account
AWS_ACCOUNT_FOR_ENV = {
    DEFAULT_WORKSPACE: "dev",
    "int": "test",
    "ref": "test",
    "prod": "prod",
}


def generate_jwt(
    jwt_private_key: str,
    oauth_url: str,
    api_key: str,
    nonce: str,
    expires: time.time,
    kid: str,
):
    payload = {
        "iss": api_key,
        "sub": api_key,
        "aud": oauth_url,
        "jti": nonce,
        "exp": expires,
    }
    return jwt.encode(payload, jwt_private_key, algorithm="RS512", headers={"kid": kid})


def oauth_access_token(api_key, jwt_private_key, oauth_url, kid):
    nonce = f"correlation-id-{uuid4()}"
    key = jwt_private_key

    jwt_token = generate_jwt(
        jwt_private_key=key,
        oauth_url=oauth_url,
        api_key=api_key,
        nonce=nonce,
        expires=time.time() + 30,
        kid=kid,
    )

    response = requests.post(
        url=oauth_url,
        headers={"content-type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": jwt_token,
        },
    )
    if response.status_code != 200:
        return False, response.text
    assert response.status_code == 200, response.text
    oauth_token = json.loads(response.text)["access_token"]
    return True, oauth_token


def aws_account_id_from_profile(env: str):
    account = AWS_ACCOUNT_FOR_ENV[env]
    profile_name = f"nhsd-nrlf-{account}-admin"

    session = botocore.session.Session()
    profiles = session.full_config["profiles"]

    assert profile_name in profiles, f"Missing AWS profile '{profile_name}'"
    profile = profiles[profile_name]
    account_id = profile["aws_account_id"]

    return account_id


def aws_read_ssm_apigee_proxy(session, env: str):
    ssm_client = session.client("ssm")
    param_name = f"/nhsd-nrlf--{env}/apigee-proxy"
    try:
        param = ssm_client.get_parameter(Name=param_name)
    except ssm_client.exceptions.ParameterNotFound as e:
        raise Exception(f"Parameter Not Found: {param_name}") from e
    return param["Parameter"]["Value"]


def aws_read_apigee_app_secrets(session, secret_id: str):
    secrets_client = session.client("secretsmanager")

    response = secrets_client.get_secret_value(SecretId=secret_id)
    secret = json.loads(response["SecretString"])

    api_key = secret["api_key"]
    oauth_url = secret["oauth_url"]
    kid = secret["kid"]
    private_key = base64.b64decode(secret["private_key"])
    # Check other required fields are present
    for field in ["apigee_url", "public_key"]:
        secret[field]  # Will raise KeyError if missing

    return api_key, oauth_url, kid, private_key


def aws_session_assume_terraform_role(account_id):
    sts_client = boto3.client("sts")

    assumed_role = sts_client.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/terraform",
        RoleSessionName=f"smoke-test-{datetime.utcnow().timestamp()}",
    )
    session = boto3.Session(
        aws_access_key_id=assumed_role["Credentials"]["AccessKeyId"],
        aws_secret_access_key=assumed_role["Credentials"]["SecretAccessKey"],
        aws_session_token=assumed_role["Credentials"]["SessionToken"],
    )

    return session


@cache
def get_oauth_token(session, account: str, env: str):
    secret_name = f"nhsd-nrlf--{account}--{env}--apigee-app--smoke-test"
    try:
        api_key, oauth_url, kid, private_key = aws_read_apigee_app_secrets(
            session, secret_name
        )
    except Exception as e:
        raise Exception(f"Cannot find secret {secret_name}") from e

    success, oauth_token = oauth_access_token(api_key, private_key, oauth_url, kid)
    assert success, oauth_token

    return oauth_token


def _prepare_base_request(env: str, actor: str) -> tuple[str, dict]:
    if os.environ.get("RUNNING_IN_CI"):
        account_id = get_terraform_json()["assume_account_id"]["value"]
    else:
        account_id = aws_account_id_from_profile(env)
    account = AWS_ACCOUNT_FOR_ENV[env]

    session = aws_session_assume_terraform_role(account_id)

    apigee_base_url = aws_read_ssm_apigee_proxy(session, env)
    if apigee_base_url.strip() == "":
        pytest.skip("Smoke Test Disabled: No APIGEE Proxy defined")

    oauth_token = get_oauth_token(session, account, env)

    base_url = f"https://{apigee_base_url}/nrl-{actor}-api"
    headers = {
        "accept": "application/json; version=1.0",
        "authorization": f"Bearer {oauth_token}",
        "x-correlation-id": f"SMOKE:{uuid4()}",
        "x-request-id": f"{uuid4()}",
    }
    return base_url, headers


@pytest.fixture
def environment() -> str:
    env = os.environ.get("TF_WORKFLOW_ID", DEFAULT_WORKSPACE).strip().lower()
    return env


@pytest.mark.parametrize(
    "actor",
    [
        "producer",
    ],
)
@pytest.mark.smoke
def test_search_endpoints(actor, environment):
    base_url, headers = _prepare_base_request(env=environment, actor=actor)

    patient_id = urllib.parse.quote(f"https://fhir.nhs.uk/Id/nhs-number|9278693472")
    url = f"{base_url}/FHIR/R4/DocumentReference?subject={patient_id}"
    headers["NHSD-End-User-Organisation-ODS"] = "RJ11"
    response = requests.get(url=url, headers=headers)
    assert response.status_code == 200, response.text


if __name__ == "__main__":
    env = sys.argv[1]
    account = sys.argv[2]

    account_id = aws_account_id_from_profile(account)

    session = aws_session_assume_terraform_role(account_id)

    print(get_oauth_token(session, env=env, account=account))
