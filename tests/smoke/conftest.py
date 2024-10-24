import json

import boto3
import pytest

from scripts.aws_session_assume import get_boto_session
from tests.smoke.environment import EnvironmentConfig, SmokeTestParameters
from tests.utilities.api_clients import ConsumerTestClient, ProducerTestClient


@pytest.fixture(autouse=True, scope="session")
def environment_config():
    return EnvironmentConfig()


@pytest.fixture(scope="session")
def boto_session(environment_config: EnvironmentConfig) -> boto3.Session:
    return get_boto_session(environment_config.env_name)


@pytest.fixture(autouse=True, scope="session")
def smoke_test_parameters(
    environment_config: EnvironmentConfig, boto_session: boto3.Session
) -> SmokeTestParameters:
    parameters_name = environment_config.get_parameters_name()

    secretsmanager = boto_session.client("secretsmanager", region_name="eu-west-2")
    secret_value = secretsmanager.get_secret_value(SecretId=parameters_name)

    parameters = json.loads(secret_value["SecretString"])

    return SmokeTestParameters(parameters)


@pytest.fixture(autouse=True, scope="session")
def producer_client(
    environment_config: EnvironmentConfig, smoke_test_parameters: SmokeTestParameters
) -> ProducerTestClient:
    return ProducerTestClient(
        config=environment_config.to_client_config(smoke_test_parameters)
    )


@pytest.fixture(autouse=True, scope="session")
def consumer_client(
    environment_config: EnvironmentConfig, smoke_test_parameters: SmokeTestParameters
) -> ConsumerTestClient:
    return ConsumerTestClient(
        config=environment_config.to_client_config(smoke_test_parameters)
    )


@pytest.fixture
def test_nhs_numbers(smoke_test_parameters: SmokeTestParameters) -> list[str]:
    return smoke_test_parameters.test_nhs_numbers
