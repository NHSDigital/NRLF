import os
import re
import urllib.parse
from uuid import uuid4

import fire
import pytest
import requests

from helpers.aws_session import DEFAULT_WORKSPACE
from helpers.oauth import APIGEE_ENV_FOR_ENV, DEFAULT_APP_ALIAS, token

ENV_NAME_RE = re.compile("^(?P<env>\w+)(-(?P<sandbox>sandbox)?)?$")

APIGEE_BASE_URL = "api.service.nhs.uk"


def aws_read_ssm_apigee_proxy(session, env: str):
    ssm_client = session.client("ssm")
    param_name = f"/nhsd-nrlf--{env}/apigee-proxy"
    try:
        param = ssm_client.get_parameter(Name=param_name)
    except ssm_client.exceptions.ParameterNotFound as e:
        raise Exception(f"Parameter Not Found: {param_name}") from e
    return param["Parameter"]["Value"]


def create_apigee_url(apigee_env: str, actor: str):
    base_url = ".".join(filter(bool, (apigee_env, APIGEE_BASE_URL)))
    return f"https://{base_url}/record-locator/{actor}"


def generate_end_user_header(env):
    if env == "prod":
        return "XXXX"
    return "RJ11"


def generate_end_user_receiver_header(env):
    if env == "prod":
        return "XXXX"
    return "DEF"


def _prepare_base_request(env: str, actor: str, app_alias: str) -> tuple[str, dict]:
    base_env = split_env_variable(env)["env"]
    oauth_token = token(env=base_env, app_alias=app_alias)
    apigee_env = APIGEE_ENV_FOR_ENV[env]
    base_url = create_apigee_url(apigee_env=apigee_env, actor=actor)
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


def split_env_variable(environment):
    result = ENV_NAME_RE.match(environment)
    if not result or environment.endswith("-"):
        raise ValueError(f"'{environment}' must be of the form 'env' or 'env-sandbox'")
    return result.groupdict()


class Smoketests:
    def manual_smoke_test(
        self, actor, environment: str, app_alias: str = DEFAULT_APP_ALIAS
    ):
        print("🏃 Running 🏃 smoke test - 🤔")  # noqa: T201
        base_url, headers = _prepare_base_request(
            env=environment, actor=actor, app_alias=app_alias
        )
        patient_id = urllib.parse.quote(f"https://fhir.nhs.uk/Id/nhs-number|9278693472")
        url = f"{base_url}/FHIR/R4/DocumentReference?subject:identifier={patient_id}"
        headers["NHSD-End-User-Organisation-ODS"] = generate_end_user_header(
            environment
        )
        headers["NHSD-End-User-Organisation"] = generate_end_user_receiver_header(
            environment
        )
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            print("🎉🎉 - Your 💨 Smoke 💨 test has passed - 🎉🎉")  # noqa: T201
        else:
            raise fire.core.FireError("The smoke test has failed 😭😭")


if __name__ == "__main__":
    fire.Fire(Smoketests)
