from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import boto3
import moto
import pytest

from cron.seed_sandbox.repository import SandboxRepository
from cron.seed_sandbox.steps import _is_sandbox_lambda, _seed_step_factory
from cron.seed_sandbox.tests.utils import (
    DummyModel,
    create_dummy_model_json_file,
    create_table,
)
from nrlf.core.model import DocumentPointer
from nrlf.core.types import DynamoDbClient


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
    "data_in_table_before_operation",
    (
        [],  # No data in table before seeding
        [{"id": "BAR"}, {"id": "BAZ"}],  # Some data in table before seeding
    ),
    ids=("No data in table before seeding", "Some data in table before seeding"),
)
@moto.mock_dynamodb()
def test__seed_step_factory(data_in_table_before_operation, temp_directory):
    item_type_name = "dummy-model"  # Maps on to DummyModel
    new_raw_data = [{"id": "SPAM"}, {"id": "EGGS"}]  # two rows of DummyModel data

    client: DynamoDbClient = boto3.client("dynamodb")
    create_table(client=client, item_type_name=item_type_name)

    repository_factory = SandboxRepository.factory(client=client, environment_prefix="")
    _repository: SandboxRepository = repository_factory(DummyModel)

    # Add initial data to table
    initial_model_data = []
    if data_in_table_before_operation:
        initial_model_data = list(
            map(DummyModel.parse_obj, data_in_table_before_operation)
        )
        _repository.create_all(initial_model_data)

    # Confirm that the database setup is as we expect
    initial_existing_items = list(map(DummyModel.parse_obj, _repository._scan()))
    assert initial_existing_items == initial_model_data

    # Create json files to read from
    template_path_to_data = str(Path(temp_directory) / "{item_type_name}.json")
    create_dummy_model_json_file(
        raw_data=new_raw_data,
        template_path_to_data=template_path_to_data,
        item_type_name=item_type_name,
    )

    # Create and the run the table seeding function
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

    # Check result
    assert dict(result) == {"message": "ok"}
    created_items = list(map(DummyModel.parse_obj, _repository._scan()))
    expected_items = list(map(DummyModel.parse_obj, new_raw_data))
    assert created_items == expected_items


@pytest.mark.parametrize(
    "item_type",
    [
        DocumentPointer,
    ],
)
def test__seed_step_factory_works_with_provided_data(item_type):
    _seed_step_factory(item_type=item_type, log=False)
