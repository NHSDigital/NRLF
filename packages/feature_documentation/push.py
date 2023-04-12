import json
from pathlib import Path
from typing import List

import boto3
from atlassian import Confluence
from nrlf.core.validators import json_loads

SECRET_NAME = "confluence/credentials"  # pragma: allowlist secret
REPORT_DIR = "report"
ENDPOINT = "https://nhsd-confluence.digital.nhs.uk"
SPACE = "DDAP"
FEATURE_DIR = "test/feature-tests/features"
TOP_PAGE_TITLE = "Feature documentation"
PAGE_TITLE = "NRLF"


def push(env_name: str = "dev") -> List[str]:
    confluence = _authenticate_to_confluence()
    top_page = _get_or_create_page(confluence=confluence, title=TOP_PAGE_TITLE)

    prod_page = _get_or_create_page(
        confluence=confluence,
        title="National Record Locator",
        parent_id=top_page["id"],
        representation="wiki",
    )

    env_page = _get_or_create_page(
        confluence=confluence,
        title=f"{env_name} - NRLF",
        parent_id=prod_page["id"],
        representation="wiki",
    )

    for filepath in _get_generated_feature_html_files():
        print(f"Uploading {filepath} to confluence under page id {env_page['id']}")
        with open(filepath, "r") as feature_file:
            body = feature_file.read()
        confluence.update_or_create(
            parent_id=env_page["id"],
            title=f"{filepath.stem} in {env_name}",  # title must be globally unique or it will overwrite other pages
            body=body,
            representation="storage",
        )


def _authenticate_to_confluence():
    session = boto3.session.Session()
    client = session.client("secretsmanager")
    auth = json_loads(client.get_secret_value(SecretId=SECRET_NAME).get("SecretString"))
    return Confluence(
        url=ENDPOINT, username=auth["username"], password=auth["password"]
    )


def _get_or_create_page(confluence, title, body="", **create_kwargs):
    if confluence.page_exists(space=SPACE, title=title):
        page = confluence.get_page_by_title(space=SPACE, title=title)
    else:
        page = confluence.create_page(
            space=SPACE, title=title, body=body, **create_kwargs
        )
    return page


def _get_generated_feature_html_files():
    yield from Path(f"{REPORT_DIR}/nrlf/").glob("*.html")
