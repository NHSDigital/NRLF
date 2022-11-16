import pytest
import requests

PORT = "8000"


@pytest.mark.sandbox
def test_healthcheck():
    response = requests.get(f"http://localhost:{PORT}/_status")
    response.raise_for_status()
    api_response = response.json()
    assert api_response == {"message": "ok"}
