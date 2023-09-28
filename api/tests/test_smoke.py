import json
import os
import re
import urllib.parse
from uuid import uuid4

import fire
import pytest
import requests

from helpers.aws_session import DEFAULT_WORKSPACE
from helpers.oauth import (
    APIGEE_ENV_FOR_ENV,
    DEFAULT_APP_ALIAS,
    NRL_SYNC_APP_ALIAS,
    token,
)

ENV_NAME_RE = re.compile(r"^(?P<env>\w+)(-(?P<sandbox>sandbox)?)?$")

APIGEE_BASE_URL = "api.service.nhs.uk"
API_PATH = "/FHIR/R4/DocumentReference"
PATIENT_IDENTIFIER = "https://fhir.nhs.uk/Id/nhs-number|9278693472"
DOCUMENT_REFERENCE_IDENTIFIER_1 = "RJ11.SMOKETEST-2742179658"
DOCUMENT_REFERENCE_IDENTIFIER_2 = "RJ11.SMOKETEST-1234567892"
DOC_REF_TEMPLATE = {
    "resourceType": "DocumentReference",
    "custodian": {
        "identifier": {
            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
            "value": "RJ11.SMOKETEST",
        }
    },
    "subject": {
        "identifier": {
            "system": "https://fhir.nhs.uk/Id/nhs-number",
            "value": "2742179658",
        }
    },
    "type": {
        "coding": [{"system": "http://snomed.info/sct", "code": "861421000000108"}]
    },
    "content": [
        {
            "attachment": {
                "contentType": "application/pdf",
                "url": "https://example.org/my-doc.pdf",
            }
        }
    ],
    "status": "current",
    "date": "2023-05-02T12:00:00.000Z",
}


def search(base_url: str, headers: dict):
    patient_id = urllib.parse.quote(PATIENT_IDENTIFIER)
    url = f"{base_url}?subject:identifier={patient_id}"
    return requests.get(url=url, headers=headers)


def sync_create(base_url: str, headers: dict):
    doc_ref = {**DOC_REF_TEMPLATE, "id": DOCUMENT_REFERENCE_IDENTIFIER_1}
    return requests.post(url=base_url, headers=headers, data=json.dumps(doc_ref))


def sync_supersede(base_url: str, headers: dict):
    doc_ref = {
        "id": DOCUMENT_REFERENCE_IDENTIFIER_2,
        **DOC_REF_TEMPLATE,
        **{
            "relatesTo": [
                {
                    "code": "replaces",
                    "target": {
                        "type": "DocumentReference",
                        "identifier": {"value": DOCUMENT_REFERENCE_IDENTIFIER_1},
                    },
                }
            ],
        },
    }
    return requests.post(url=base_url, headers=headers, data=json.dumps(doc_ref))


def delete(base_url: str, headers: dict):
    url = f"{base_url}/{DOCUMENT_REFERENCE_IDENTIFIER_2}"
    return requests.delete(url=url, headers=headers)


REQUEST_METHODS = {
    DEFAULT_APP_ALIAS: [search],
    NRL_SYNC_APP_ALIAS: [sync_create, sync_supersede, delete],
}


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
    return f"https://{base_url}/record-locator/{actor}/{API_PATH}"


def generate_end_user_header(env):
    if env == "prod":
        return "XXXX"
    return "RJ11"


def generate_end_user_receiver_header(env):
    if env == "prod":
        return "XXXX"
    return "SMOKETEST"


def _prepare_base_request(env: str, actor: str, app_alias: str) -> tuple[str, dict]:
    base_env = split_env_variable(env)["env"]
    oauth_token = token(env=base_env, app_alias=app_alias)
    apigee_env = APIGEE_ENV_FOR_ENV[env]
    base_url = create_apigee_url(
        apigee_env=apigee_env if apigee_env != "prod" else "", actor=actor
    )
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


def is_2xx(status_code: int):
    return 200 <= status_code < 300


class Smoketests:
    def manual_smoke_test(
        self, actor, environment: str, app_alias: str = DEFAULT_APP_ALIAS
    ):
        print("🏃 Running 🏃 smoke test - 🤔")  # noqa: T201
        base_url, headers = _prepare_base_request(
            env=environment, actor=actor, app_alias=app_alias
        )
        headers["NHSD-End-User-Organisation-ODS"] = generate_end_user_header(
            environment
        )
        headers["NHSD-End-User-Organisation"] = generate_end_user_receiver_header(
            environment
        )
        for request_method in REQUEST_METHODS[app_alias]:
            response = request_method(base_url=base_url, headers=headers)
            if is_2xx(response.status_code):
                print(  # noqa: T201
                    f"🎉🎉 - Your 💨 Smoke 💨 test for method '{request_method.__name__}' has passed - 🎉🎉"
                )
            else:
                raise fire.core.FireError(
                    f"The smoke test for method '{request_method.__name__}' "
                    f"has failed with status code {response.status_code} 😭😭\n"
                    f"{response.json()}"
                )


if __name__ == "__main__":
    fire.Fire(Smoketests)
