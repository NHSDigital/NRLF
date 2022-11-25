import json
import urllib.parse

import requests
from lambda_utils.tests.unit.utils import make_aws_event

from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json

DEFAULT_VERSION = 1.0


def _document_pointer_api_request(
    method: str,
    product: str,
    version: int = DEFAULT_VERSION,
    path_params: list = [],
    sandbox=False,
    **request_kwargs,
):
    base_url = f'{get_terraform_json()["api_base_urls"]["value"][product]}'
    if sandbox:
        base_url = f"http://localhost:8000/{product}"
    url = f"{base_url}/DocumentReference"
    for value in path_params:
        url += f"/{urllib.parse.quote(value)}"

    request_kwargs["headers"] = {
        **request_kwargs.get("headers", {}),
        "Accept": f"version={version}",
    }
    return requests.request(method=method, url=url, **request_kwargs)


def _authoriser_lambda_request(
    product: str,
    event: dict,
    version: int = DEFAULT_VERSION,
):
    function_name = f'nhsd-nrlf--{get_terraform_json()["workspace"]["value"]}--api--{product}--authoriser'
    session = new_aws_session()
    client = session.client("lambda")

    response = client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(event),
    )

    return json.loads(response["Payload"].read().decode("utf-8"))


def producer_create_api_request(
    data: dict,
    headers: dict,
    version: str = DEFAULT_VERSION,
    sandbox=False,
):
    return _document_pointer_api_request(
        product="producer",
        method="POST",
        version=version,
        data=data,
        headers=headers,
        sandbox=sandbox,
    )


def producer_update_api_request(
    path_params: list,
    data: dict,
    headers: dict,
    version: str = DEFAULT_VERSION,
    sandbox=False,
):
    return _document_pointer_api_request(
        product="producer",
        method="PUT",
        version=version,
        data=data,
        headers=headers,
        path_params=path_params,
        sandbox=sandbox,
    )


def producer_read_api_request(
    path_params: list,
    headers: dict,
    version: str = DEFAULT_VERSION,
    sandbox=False,
):
    return _document_pointer_api_request(
        product="producer",
        method="GET",
        version=version,
        path_params=path_params,
        headers=headers,
        sandbox=sandbox,
    )


def producer_delete_api_request(
    path_params: list,
    headers: dict,
    version: str = DEFAULT_VERSION,
    sandbox=False,
):
    return _document_pointer_api_request(
        product="producer",
        method="DELETE",
        version=version,
        path_params=path_params,
        headers=headers,
        sandbox=sandbox,
    )


def consumer_read_api_request(
    path_params: list,
    headers: dict,
    version: str = DEFAULT_VERSION,
    sandbox=False,
):
    return _document_pointer_api_request(
        product="consumer",
        method="GET",
        version=version,
        path_params=path_params,
        headers=headers,
        sandbox=sandbox,
    )


def producer_search_api_request(
    params: dict,
    headers: dict,
    version: str = DEFAULT_VERSION,
    sandbox=False,
):

    return _document_pointer_api_request(
        product="producer",
        method="GET",
        version=version,
        params=params,
        headers=headers,
        sandbox=sandbox,
    )


def consumer_search_api_request(
    params: dict,
    headers: dict,
    version: str = DEFAULT_VERSION,
    sandbox=False,
):

    return _document_pointer_api_request(
        product="consumer",
        method="GET",
        version=version,
        params=params,
        headers=headers,
        sandbox=sandbox,
    )


def consumer_search_api_request_post(
    path_params: list,
    data: dict,
    headers: dict,
    version: str = DEFAULT_VERSION,
    sandbox=False,
):

    return _document_pointer_api_request(
        product="consumer",
        method="POST",
        version=version,
        data=data,
        path_params=path_params,
        headers=headers,
        sandbox=sandbox,
    )


def producer_authoriser_lambda(
    event: dict,
    version: str = DEFAULT_VERSION,
):

    return _authoriser_lambda_request(product="producer", event=event, version=version)


def consumer_authoriser_lambda(
    event: dict,
    version: str = DEFAULT_VERSION,
):

    return _authoriser_lambda_request(product="consumer", event=event, version=version)
