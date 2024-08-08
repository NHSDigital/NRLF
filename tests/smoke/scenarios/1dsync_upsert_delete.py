from tests.smoke.setup import build_document_reference
from tests.utilities.api_clients import ProducerTestClient


def test_1dsync_upsert_delete(
    producer_client: ProducerTestClient, test_nhs_numbers: list[str]
):
    """
    Smoke test scenario for 1dsync upsert and delete behaviour
    """
    test_docref = build_document_reference(nhs_number=test_nhs_numbers[0])

    # TODO-NOW - Use a different ODS code, App ID and add permissions headers for 1DSYNC
    # ???? How will that work if we're going via APIGEE? Different app?

    for attempts in range(0, 5):
        try:
            test_docref = build_document_reference(nhs_number=test_nhs_numbers[0])
            test_docref.id = f"SMOKETEST-1dsync_upsert_delete_pointer_{attempts}"
            upsert_response = producer_client.upsert(test_docref.dict())
            assert upsert_response.ok
            assert upsert_response.headers["Location"].split("/")[-1] == test_docref.id
        finally:
            delete_response = producer_client.delete(test_docref.id)
            assert delete_response.ok

            read_response = producer_client.read(test_docref.id)
            assert read_response.status_code == 404
