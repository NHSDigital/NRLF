from typing import Any, Generator

import pytest

from tests.smoke.setup import upsert_test_pointer
from tests.utilities.api_clients import ConsumerTestClient, ProducerTestClient


@pytest.fixture(autouse=True)
def test_pointer_id(
    test_nhs_numbers: list[str], producer_client: ProducerTestClient
) -> Generator[str, Any, None]:
    test_pointer = upsert_test_pointer(
        "SMOKETEST-test_read_pointer",
        nhs_number=test_nhs_numbers[0],
        producer_client=producer_client,
    )
    # TODO-NOW - Does yield return here if the test fails with an exception?
    yield test_pointer.id
    producer_client.delete(test_pointer.id)


def test_read_pointer(consumer_client: ConsumerTestClient, test_pointer_id: str):
    # Read a pointer from the API
    response = consumer_client.read(test_pointer_id)
    assert response.ok
