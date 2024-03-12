import os

import pytest
from pydantic import ValidationError

from nrlf.core.config import AuthorizerConfig, Config


def test_config_valid():
    # Arrange
    env_vars = {
        "AWS_REGION": "eu-west-2",
        "PREFIX": "nrlf",
        "ENVIRONMENT": "production",
        "SPLUNK_INDEX": "logs",
        "SOURCE": "app",
    }

    # Act
    config = Config(**env_vars)

    # Assert
    assert env_vars["AWS_REGION"] == config.AWS_REGION
    assert env_vars["PREFIX"] == config.PREFIX
    assert env_vars["ENVIRONMENT"] == config.ENVIRONMENT
    assert env_vars["SPLUNK_INDEX"] == config.SPLUNK_INDEX
    assert env_vars["SOURCE"] == config.SOURCE


def test_config_missing_env_vars():
    # Arrange
    env_vars = {}
    _current_env_vars = os.environ.copy()
    os.environ.clear()

    # Act & Assert
    with pytest.raises(ValidationError):
        Config(**env_vars)

    os.environ.update(_current_env_vars)


def test_config_invalid_env_vars():
    # Arrange
    env_vars = {
        "AWS_REGION": "eu-west-2",
        "PREFIX": "nrlf",
        "ENVIRONMENT": "production",
        "SOURCE": "app",
    }
    # Missing SPLUNK_INDEX

    _current_env_vars = os.environ.copy()
    os.environ.clear()

    # Act & Assert
    with pytest.raises(ValidationError) as e:
        Config(**env_vars)

    assert "SPLUNK_INDEX" in str(e.value)
    assert "field required" in str(e.value)

    os.environ.update(_current_env_vars)


def test_config_reads_from_env_variables():
    # Arrange
    env_vars = {
        "AWS_REGION": "eu-west-2",
        "PREFIX": "nrlf",
        "ENVIRONMENT": "production",
        "SPLUNK_INDEX": "logs",
        "SOURCE": "app",
    }

    for k, v in env_vars.items():
        os.environ[k] = v

    # Act
    config = Config()

    # Assert
    assert env_vars["AWS_REGION"] == config.AWS_REGION
    assert env_vars["PREFIX"] == config.PREFIX
    assert env_vars["ENVIRONMENT"] == config.ENVIRONMENT
    assert env_vars["SPLUNK_INDEX"] == config.SPLUNK_INDEX
    assert env_vars["SOURCE"] == config.SOURCE

    for k in env_vars:
        del os.environ[k]


def test_authorizer_config_valid():
    # Arrange
    env_vars = {
        "AWS_REGION": "eu-west-2",
        "PREFIX": "nrlf",
        "ENVIRONMENT": "production",
        "SPLUNK_INDEX": "logs",
        "SOURCE": "app",
        "AUTH_STORE": "auth-store",
    }

    # Act
    config = AuthorizerConfig(**env_vars)

    # Assert
    assert env_vars["AUTH_STORE"] == config.AUTH_STORE
