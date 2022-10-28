import requests

from feature_tests.steps.aws.resources.common import get_terraform_json


def create_document_pointer_api_request(body: str, headers: dict, version: str = "1.0"):
    url = f'{get_terraform_json()["api_base_urls"]["value"]["producer"]}/DocumentReference'
    return requests.post(
        url=url, headers={**headers, "Accept": f"version={version}"}, data=body
    )
