from typing import List
import pytest
from api.consumer.readDocumentReference.src.versioning import AcceptHeader

def test_api_version_parsing():
    event = {"headers": {"Accept": "version=1", "test": "test"}}
    accept_header = AcceptHeader(event)
    assert accept_header.version == "1"
