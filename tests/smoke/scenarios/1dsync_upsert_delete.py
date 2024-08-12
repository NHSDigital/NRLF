import pytest

from nrlf.core.constants import PERMISSION_ALLOW_ALL_POINTER_TYPES
from tests.smoke.environment import ConnectMode, EnvironmentConfig, SmokeTestParameters
from tests.smoke.setup import build_document_reference
from tests.utilities.api_clients import ProducerTestClient


@pytest.fixture
def producer_client_1dsync(
    environment_config: EnvironmentConfig, smoke_test_parameters: SmokeTestParameters
) -> ProducerTestClient:
    client_config = environment_config.to_client_config(smoke_test_parameters)

    if environment_config.connect_mode == ConnectMode.INTERNAL:
        client_config.connection_metadata["nrl.permissions"] = [
            PERMISSION_ALLOW_ALL_POINTER_TYPES
        ]
        client_config.connection_metadata["nrl.app-id"] = "SMOKETEST_1DSYNC"

    return ProducerTestClient(config=client_config)


def test_1dsync_upsert_delete(
    producer_client_1dsync: ProducerTestClient,
    smoke_test_parameters: SmokeTestParameters,
    test_nhs_numbers: list[str],
):
    """
    Smoke test scenario for 1dsync upsert and delete behaviour
    """
    test_ods_code = smoke_test_parameters.ods_code
    test_docref = build_document_reference(
        nhs_number=test_nhs_numbers[0], custodian=test_ods_code
    )

    for attempts in range(0, 5):
        try:
            test_docref.id = (
                f"{test_ods_code}-smoketest_1dsync_upsert_delete_pointer_{attempts}"
            )
            upsert_response = producer_client_1dsync.upsert(test_docref.dict())
            assert upsert_response.ok
            assert upsert_response.headers["Location"].split("/")[-1] == test_docref.id
        finally:
            delete_response = producer_client_1dsync.delete(test_docref.id)

            assert (
                delete_response.ok
            ), f"Failed to delete document reference with ID: {test_docref.id}. It will need to be deleted manually if it still exists."

            read_response = producer_client_1dsync.read(test_docref.id)
            assert read_response.status_code == 404
