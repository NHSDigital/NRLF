from typing import List
import pytest
from api.consumer.searchViaPostDocumentReference.src.versioning import AcceptHeader
from lambda_utils.tests.unit.utils import make_aws_event


@pytest.mark.parametrize(
    "event, expected_version",
    [(make_aws_event(), "1"), (make_aws_event(version="2"), "2")],
)
def test_api_version_parsing(event: dict, expected_version: str):
    accept_header = AcceptHeader(event)
    assert accept_header.version == expected_version
