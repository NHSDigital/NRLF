import json
import os
from uuid import uuid4

import pytest
import requests
from lambda_utils.tests.unit.status_test_utils import OK
from lambda_utils.tests.unit.utils import make_aws_event
from nrlf.core.validators import json_loads

from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json


@pytest.fixture(scope="session")
def client():
    session = new_aws_session()
    return session.client("lambda")


def get_lambda_name(actor: str) -> str:
    return get_terraform_json()["status_lambda_function_names"]["value"][actor]


def get_api_url(actor: str) -> str:
    return get_terraform_json()["api_base_urls"]["value"][actor]


@pytest.fixture(scope="session")
def account_name() -> str:
    return get_terraform_json()["account_name"]["value"]


@pytest.fixture(scope="session")
def client_cert_dir() -> str:
    return os.path.normpath(
        os.path.join(os.path.dirname(f"{__file__}"), "../../truststore/client")
    )


@pytest.mark.parametrize(
    "actor",
    [
        "producer",
        "consumer",
    ],
)
@pytest.mark.integration
def test_status_lambda(actor, client):
    uid = str(uuid4())
    correlation_id = f"test_status_lambda:{uid}-{actor}"

    event = json.dumps(
        make_aws_event(
            headers={
                "nhsd-correlation-id": correlation_id,
                "x-correlation-id": correlation_id,
                # "x-request-id": uid,
            }
        )
    )
    function_name = get_lambda_name(actor=actor)
    aws_response = client.invoke(FunctionName=function_name, Payload=event)
    lambda_response = json_loads(aws_response["Payload"].read())
    assert lambda_response == OK, lambda_response


@pytest.mark.parametrize(
    "headers",
    [
        # No headers
        {},
        # Some logging headers
        {
            "nhsd-correlation-id": f"test_status_api:{uuid4()}",
        },
        # All logging headers
        {
            "nhsd-correlation-id": f"test_status_api:{uuid4()}",
            "x-correlation-id": f"test_status_api:{uuid4()}",
            "x-request-id": f"test_status_api:{uuid4()}",
        },
    ],
)
@pytest.mark.parametrize(
    "actor",
    [
        "producer",
        "consumer",
    ],
)
@pytest.mark.integration
def test_status_api(actor, headers, account_name, client_cert_dir):
    headers = {k: f"{v}-{actor}" for k, v in headers.items()}
    url = f"{get_api_url(actor=actor)}/_status"
    response = requests.get(
        url=url,
        headers=headers,
        cert=(
            f"{client_cert_dir}/{account_name}.crt",
            f"{client_cert_dir}/{account_name}.key",
        ),
    )
    assert response.status_code == OK["statusCode"], response.text
    assert response.text == OK["body"]
