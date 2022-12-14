from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import boto3
import moto
import pytest
from nrlf.core.model import AuthConsumer, AuthProducer, DocumentPointer
from nrlf.core.types import DynamoDbClient

from cron.seed_sandbox.repository import SandboxRepository
from cron.seed_sandbox.steps import _is_sandbox_lambda, _seed_step_factory
from cron.seed_sandbox.tests.utils import (
    DummyModel,
    create_local_raw_data,
    create_table,
    sort_models,
)


@pytest.fixture
def temp_directory():
    with TemporaryDirectory() as dir:
        yield dir


@pytest.mark.parametrize(
    ["function_name", "environment", "prefix", "expected_result"],
    (
        ["foo", "bar", "baz", False],
        ["foo-sandbox", "bar", "baz", False],
        ["foo", "bar-sandbox", "baz", False],
        ["foo", "bar", "baz-sandbox", False],
        ["foo-sandbox", "bar-sandbox", "baz", False],
        ["foo-sandbox", "bar", "baz-sandbox", False],
        ["foo", "bar-sandbox", "baz-sandbox", False],
        ["foo-sandbox", "bar-sandbox", "baz-sandbox", True],
    ),
)
def test__is_sandbox_lambda(function_name, environment, prefix, expected_result):
    mock_context = mock.Mock()
    mock_context.function_name = function_name
    actual_result = _is_sandbox_lambda(
        context=mock_context, environment=environment, prefix=prefix
    )
    assert actual_result is expected_result


@pytest.mark.parametrize(
    "initial_raw_data",
    ([], [{"id": "BAR"}, {"id": "BAZ"}], [{"id": "SPAM"}, {"id": "EGGS"}]),
)
@moto.mock_dynamodb()
def test__seed_step_factory(initial_raw_data, temp_directory):
    item_type_name = "dummy-model"
    new_raw_data = [{"id": "SPAM"}, {"id": "EGGS"}]
    new_model_data = sort_models(map(DummyModel.parse_obj, new_raw_data))
    initial_model_data = sort_models(map(DummyModel.parse_obj, initial_raw_data))
    dynamodb_client: DynamoDbClient = boto3.client("dynamodb")
    repository_factory = SandboxRepository.factory(
        client=dynamodb_client, environment_prefix=""
    )
    template_path_to_data = str(Path(temp_directory) / "{item_type_name}.json")

    # Given
    create_table(client=dynamodb_client, item_type_name=item_type_name)
    _repository: SandboxRepository = repository_factory(DummyModel)
    if initial_raw_data:
        _repository.create_all(initial_model_data)
    item_iter = _repository._scan()
    initial_existing_items = sort_models(map(DummyModel.parse_obj, item_iter))
    assert initial_existing_items == initial_model_data

    create_local_raw_data(
        raw_data=new_raw_data,
        template_path_to_data=template_path_to_data,
        item_type_name=item_type_name,
    )

    # When
    seeder = _seed_step_factory(
        item_type=DummyModel, template_path_to_data=template_path_to_data, log=False
    )
    result = seeder(
        data=None,
        context=None,
        event=None,
        dependencies={"repository_factory": repository_factory},
        logger=None,
    )

    # Then
    assert dict(result) == {"message": "ok"}
    item_iter = _repository._scan()
    new_existing_items = sort_models(map(DummyModel.parse_obj, item_iter))
    assert new_existing_items == new_model_data


@pytest.mark.parametrize("item_type", [AuthConsumer, AuthProducer, DocumentPointer])
def test__seed_step_factory_works_with_provided_data(item_type):
    _seed_step_factory(item_type=item_type, log=False)
