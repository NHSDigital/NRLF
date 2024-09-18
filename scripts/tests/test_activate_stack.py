import json
import os

import pytest

from scripts.activate_stack import _parse_env_config, activate_stack


@pytest.fixture
def mock_secretsmanager(mocker):
    mock_secretsmanager = mocker.MagicMock()
    mock_env_configs = {}
    mock_secretsmanager.get_secret_value.side_effect = lambda SecretId: {
        "SecretId": SecretId,
        "SecretString": json.dumps(mock_env_configs[SecretId]),
    }
    mock_secretsmanager.create_secret.side_effect = lambda Name, SecretString: {
        mock_env_configs.update({Name: json.loads(SecretString)})
    }
    mock_secretsmanager.put_secret_value.side_effect = lambda SecretId, SecretString: {
        mock_env_configs.update({SecretId: json.loads(SecretString)})
    }

    return mock_secretsmanager


@pytest.fixture
def mock_apigw(mocker):
    mock_apigw = mocker.MagicMock()

    mock_rest_apis = [
        {"name": "nhsd-nrlf--test-stack-1--consumer", "id": "consumer-id"},
        {"name": "nhsd-nrlf--test-stack-1--producer", "id": "producer-id"},
        {"name": "nhsd-nrlf--test-stack-2--consumer", "id": "consumer-id"},
        {"name": "nhsd-nrlf--test-stack-2--producer", "id": "producer-id"},
    ]

    mock_apigw.get_rest_apis.return_value = {"items": mock_rest_apis}
    return mock_apigw


@pytest.fixture
def mock_apigwv2(mocker):
    mock_apigwv2 = mocker.MagicMock()

    mock_api_mappings = {
        "consumer-id": {"ApiMappingKey": "consumer", "ApiMappingId": "consumer-id"},
        "producer-id": {"ApiMappingKey": "producer", "ApiMappingId": "producer-id"},
    }

    mock_apigwv2.get_api_mappings.return_value = {"Items": mock_api_mappings.values()}

    return mock_apigwv2


@pytest.fixture(scope="function")
def mock_boto_session(mocker, mock_secretsmanager, mock_apigw, mock_apigwv2):
    mock_boto_session = mocker.MagicMock()
    mock_boto_session.client.side_effect = lambda service_name: {
        "secretsmanager": mock_secretsmanager,
        "apigateway": mock_apigw,
        "apigatewayv2": mock_apigwv2,
    }[service_name]
    return mock_boto_session


def _create_mock_env_config():
    return {
        "lock-state": "open",
        "active-stack": "test-stack-1",
        "active-version": "v1",
        "inactive-stack": "test-stack-2",
        "inactive-version": "v2",
        "domain-name": "test.domain.name",
    }


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
        "active-version": "v2",
        "inactive-stack": "test-stack-1",
        "inactive-version": "v1",
    }
    assert result["SecretString"] == json.dumps(expected_env_config)


def test_lock_state_not_open(mock_boto_session, mock_secretsmanager):
    inital_env_config = {
        **_create_mock_env_config(),
        "lock-state": "locked",
    }
    mock_secretsmanager.create_secret(
        Name="nhsd-nrlf--locked--env-config", SecretString=json.dumps(inital_env_config)
    )

    with pytest.raises(SystemExit) as excinfo:
        activate_stack("test-stack-1", "locked", session=mock_boto_session)

    assert excinfo.value.code == 1
    result = mock_secretsmanager.get_secret_value(
        SecretId="nhsd-nrlf--locked--env-config"  # pragma: allowlist secret
    )
    assert result["SecretString"] == json.dumps(inital_env_config)


def test_stack_already_active(mock_boto_session, mock_secretsmanager):
    intial_env_config = {
        **_create_mock_env_config(),
        "inactive-stack": "test-stack-1",
        "active-stack": "test-stack-2",
    }
    mock_secretsmanager.create_secret(
        Name="nhsd-nrlf--already-active--env-config",
        SecretString=json.dumps(intial_env_config),
    )

    with pytest.raises(SystemExit) as excinfo:
        activate_stack("test-stack-2", "already-active", session=mock_boto_session)

    assert excinfo.value.code == 1
    result = mock_secretsmanager.get_secret_value(
        SecretId="nhsd-nrlf--already-active--env-config"  # pragma: allowlist secret
    )
    assert result["SecretString"] == json.dumps(intial_env_config)


def test_parse_env_config_valid():
    valid_config = json.dumps(_create_mock_env_config())
    result = _parse_env_config(valid_config)
    assert result == _create_mock_env_config()


def test_parse_env_config_empty():
    with pytest.raises(ValueError):
        _parse_env_config("")


def test_parse_env_config_invalid_json():
    with pytest.raises(ValueError):
        _parse_env_config("this is not JSON!")


def test_parse_env_config_missing_params():
    with pytest.raises(ValueError):
        _parse_env_config(json.dumps({"lock-state": "open"}))


def test_parse_env_config_invalid_lock_state():
    with pytest.raises(ValueError):
        _parse_env_config(
            json.dumps({**_create_mock_env_config(), "lock-state": "invalid"})
        )
