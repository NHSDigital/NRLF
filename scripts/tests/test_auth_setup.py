import os
from contextlib import contextmanager
from typing import Generator

import boto3
import moto
import pytest
import yaml
from nrlf.core.model import AuthBase
from nrlf.core.repository import to_kebab_case
from nrlf.core.types import DynamoDbClient

from scripts.auth_setup import AuthRepository

DEFAULT_ATTRIBUTE_DEFINITIONS = [{"AttributeName": "id", "AttributeType": "S"}]
DEFAULT_KEY_SCHEMA = [{"AttributeName": "id", "KeyType": "HASH"}]
TABLE_NAME = to_kebab_case(AuthBase.__name__)
API_VERSION = 1


@contextmanager
def mock_dynamodb() -> Generator[DynamoDbClient, None, None]:
    with moto.mock_dynamodb():
        client: DynamoDbClient = boto3.client("dynamodb")
        client.create_table(
            AttributeDefinitions=DEFAULT_ATTRIBUTE_DEFINITIONS,
            TableName=TABLE_NAME,
            KeySchema=DEFAULT_KEY_SCHEMA,
            BillingMode="PAY_PER_REQUEST",
        )
        yield client


def test_recreate_auths_producer():
    actor_type = "producer"
    with mock_dynamodb() as client:
        auth_repository = AuthRepository(
            item_type=AuthBase, client=client, environment_prefix=""
        )
        auth_repository.recreate_auths(actor_type=f"{actor_type}")
        response = client.scan(TableName=TABLE_NAME)

    items = response["Items"]

    with open(
        os.path.join(os.path.dirname(__file__), f"{actor_type}.yml"), "r"
    ) as strean:
        auths = yaml.safe_load(strean)
        assert len(items) == len(auths)


def test_recreate_auths_consumer():
    actor_type = "consumer"
    with mock_dynamodb() as client:
        auth_repository = AuthRepository(
            item_type=AuthBase, client=client, environment_prefix=""
        )
        auth_repository.recreate_auths(actor_type=f"{actor_type}")
        response = client.scan(TableName=TABLE_NAME)

    items = response["Items"]

    with open(
        os.path.join(os.path.dirname(__file__), f"{actor_type}.yml"), "r"
    ) as strean:
        auths = yaml.safe_load(strean)
        assert len(items) == len(auths)


def test_recreate_auths_invalid_actor_type():
    actor_type = "prodcer"
    with pytest.raises(ValueError), mock_dynamodb() as client:
        auth_repository = AuthRepository(
            item_type=AuthBase, client=client, environment_prefix=""
        )
        auth_repository.recreate_auths(actor_type=f"{actor_type}")
