import urllib.parse

import requests

from feature_tests.steps.aws.resources.common import get_terraform_json

DEFAULT_VERSION = 1.0


def document_pointer_api_request(
    method: str,
    version: int = DEFAULT_VERSION,
    path_params: list = [],
    **request_kwargs,
):
    url = f'{get_terraform_json()["api_base_urls"]["value"]["producer"]}/DocumentReference'
    for value in path_params:
        url += f"/{urllib.parse.quote(value)}"

    request_kwargs["headers"] = {
        **request_kwargs.get("headers", {}),
        "Accept": f"version={version}",
    }
    return requests.request(method=method, url=url, **request_kwargs)
