import urllib.parse

import requests

from feature_tests.steps.aws.resources.common import get_terraform_json

DEFAULT_VERSION = 1.0


def _document_pointer_api_request(
    method: str,
    product: str,
    version: int = DEFAULT_VERSION,
    path_params: list = [],
    **request_kwargs,
):
    url = f'{get_terraform_json()["api_base_urls"]["value"][product]}/DocumentReference'
    for value in path_params:
        url += f"/{urllib.parse.quote(value)}"

    request_kwargs["headers"] = {
        **request_kwargs.get("headers", {}),
        "Accept": f"version={version}",
    }
    return requests.request(method=method, url=url, **request_kwargs)


def producer_create_api_request(
    data: dict,
    headers: dict,
    version: str = DEFAULT_VERSION,
):
    return _document_pointer_api_request(
        product="producer", method="POST", version=version, data=data, headers=headers
    )


def producer_read_api_request(
    path_params: list,
    headers: dict,
    version: str = DEFAULT_VERSION,
):
    return _document_pointer_api_request(
        product="producer",
        method="GET",
        version=version,
        path_params=path_params,
        headers=headers,
    )


def producer_delete_api_request(
    path_params: list,
    headers: dict,
    version: str = DEFAULT_VERSION,
):
    return _document_pointer_api_request(
        product="producer",
        method="DELETE",
        version=version,
        path_params=path_params,
        headers=headers,
    )


def consumer_read_api_request(
    path_params: list,
    headers: dict,
    version: str = DEFAULT_VERSION,
):
    return _document_pointer_api_request(
        product="consumer",
        method="GET",
        version=version,
        path_params=path_params,
        headers=headers,
    )


def producer_search_api_request(
    params: dict,
    headers: dict,
    version: str = DEFAULT_VERSION,
):

    return _document_pointer_api_request(
        product="producer",
        method="GET",
        version=version,
        params=params,
        headers=headers,
    )


def consumer_search_api_request(
    params: dict,
    headers: dict,
    version: str = DEFAULT_VERSION,
):

    return _document_pointer_api_request(
        product="consumer",
        method="GET",
        version=version,
        params=params,
        headers=headers,
    )
