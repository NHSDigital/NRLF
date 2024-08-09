import pytest

from tests.utilities.api_clients import ConsumerTestClient, ProducerTestClient


@pytest.mark.skip(reason="Capability statements aren't working reliably at the minute")
def test_read_api_capability_statements(
    consumer_client: ConsumerTestClient, producer_client: ProducerTestClient
):
    """
    Smoke test scenario for reading the API capability statements
    """
    read_response = consumer_client.read_capability_statement()
    assert read_response.ok

    read_response = producer_client.read_capability_statement()
    assert read_response.ok
