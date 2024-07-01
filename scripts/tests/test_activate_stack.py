import json
import os

import boto3
import pytest
from moto import mock_aws

from scripts.activate_stack import activate_stack


@pytest.fixture(scope="session")
def mock_aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="session")
def mock_boto_session(mock_aws_credentials):
    with mock_aws():
        yield boto3.Session(region_name="eu-west-2")


# @pytest.fixture(scope="session", autouse=True)
# def create_mock_aws_resources(mock_boto_session):
#    apigw = mock_boto_session.client("apigateway")
#    apis = {}
#    for stack in ["test-stack-1", "test-stack-2"]:
#        consumer = apigw.create_rest_api(name=f"nhsd-nrlf--{stack}--consumer", )
#        apigw.create_stage(restApiId=consumer["id"], deploymentId="test-1", stageName="production")
#        producer = apigw.create_rest_api(name=f"nhsd-nrlf--{stack}--producer")
#        apigw.create_stage(restApiId=producer["id"], deploymentId="test-1", stageName="production")
#
#        apis[stack] = { "consumer": consumer, "producer": producer }
#
#    active_stack = apis["test-stack-1"]
#
#    apigw_v2 = mock_boto_session.client("apigatewayv2")
#    apigw_v2.create_domain_name(DomainName="test.domain.name")
#    # TODO-NOW DOESN'T WORK - going to switch out moto for the mocks
#    apigw_v2.create_api_mapping(DomainName="test.domain.name", ApiId=active_stack["consumer"]["id"], ApiMappingKey="consumer", Stage="production")
#    apigw_v2.create_api_mapping(DomainName="test.domain.name", ApiId=active_stack["producer"]["id"], ApiMappingKey="producer", Stage="production")


@pytest.fixture(scope="session")
def mock_secretsmanager(mock_boto_session):
    yield mock_boto_session.client("secretsmanager")


@pytest.fixture(scope="session")
def mock_api_gateway(mock_boto_session):
    yield mock_boto_session.client("apigateway")


@pytest.fixture(scope="session")
def mock_api_gateway_v2(mock_boto_session):
    yield mock_boto_session.client("apigatewayv2")


def _create_mock_env_config():
    return {
        "lock-state": "open",
        "active-stack": "test-stack-1",
        "inactive-stack": "test-stack-2",
        "domain-name": "test.domain.name",
    }


@pytest.mark.skip(reason="Moto not working for apigw, going to re-write this")
def test_happy_path(mock_boto_session, mock_secretsmanager):
    mock_env_config = _create_mock_env_config()
    mock_secretsmanager.create_secret(
        Name="nhsd-nrlf--happy-path--env-config",
        SecretString=json.dumps(mock_env_config),
    )

    activate_stack("test-stack-2", "happy-path", session=mock_boto_session)

    result = mock_secretsmanager.get_secret_value(
        SecretId="nhsd-nrlf--happy-path--env-config"  # pragma: allowlist secret
    )
    expected_env_config = {
        **mock_env_config,
        "active-stack": "test-stack-2",
        "inactive-stack": "test-stack-1",
    }
    assert result["SecretString"] == json.dumps(expected_env_config)


def test_lock_state_not_open(mock_boto_session, mock_secretsmanager):
    inital_env_config = {
        "lock-state": "locked",
        "inactive-stack": "test-stack-1",
        "active-stack": "test-stack-2",
    }
    mock_secretsmanager.create_secret(
        Name="nhsd-nrlf--locked--env-config", SecretString=json.dumps(inital_env_config)
    )

    activate_stack("test-stack-1", "locked", session=mock_boto_session)

    result = mock_secretsmanager.get_secret_value(
        SecretId="nhsd-nrlf--locked--env-config"  # pragma: allowlist secret
    )
    assert result["SecretString"] == json.dumps(inital_env_config)


def test_stack_already_active(mock_boto_session, mock_secretsmanager):
    intial_env_config = {
        "lock-state": "open",
        "inactive-stack": "test-stack-1",
        "active-stack": "test-stack-2",
    }
    mock_secretsmanager.create_secret(
        Name="nhsd-nrlf--already-active--env-config",
        SecretString=json.dumps(intial_env_config),
    )

    activate_stack("test-stack-2", "already-active", session=mock_boto_session)

    result = mock_secretsmanager.get_secret_value(
        SecretId="nhsd-nrlf--already-active--env-config"  # pragma: allowlist secret
    )
    assert result["SecretString"] == json.dumps(intial_env_config)
