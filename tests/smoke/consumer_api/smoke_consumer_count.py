from typing import Any, Generator

import pytest

from tests.smoke.setup import upsert_test_pointer
from tests.utilities.api_clients import ConsumerTestClient, ProducerTestClient


@pytest.fixture(autouse=True)
def test_patient_id(
    test_nhs_numbers: list[str], producer_client: ProducerTestClient
) -> Generator[str, Any, None]:
    test_pointers = [
        upsert_test_pointer(
            f"SMOKETEST-test_count_pointers_{n}",
            nhs_number=test_nhs_numbers[0],
            producer_client=producer_client,
        )
        for n in range(0, 5)
    ]

    # TODO-NOW - Does yield return here if the test fails with an exception?
    yield test_nhs_numbers[0]

    for test_pointer in test_pointers:
        producer_client.delete(test_pointer.id)


def test_count_pointers(consumer_client: ConsumerTestClient, test_patient_id: str):
    # Count the pointer for a patient
    params = {
        "subject:identifier": f"https://fhir.nhs.uk/Id/nhs-number|{test_patient_id}"
    }
    response = consumer_client.count(params)
    assert response.ok
    assert response.json() == {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 5,
    }
