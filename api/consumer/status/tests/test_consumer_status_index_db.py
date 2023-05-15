import os
from unittest import mock

import moto
from lambda_utils.tests.unit.status_test_utils import event  # noqa: F401
from lambda_utils.tests.unit.status_test_utils import OK, SERVICE_UNAVAILABLE

from feature_tests.common.constants import TABLE_CONFIG

BASE_FIELDS = {"ENVIRONMENT": "", "SPLUNK_INDEX": "", "SOURCE": ""}


@mock.patch.dict(
    os.environ,
    {
        **BASE_FIELDS,
        "AWS_DEFAULT_REGION": "eu-west-2",
        "AWS_REGION": "eu-west-2",
        "PREFIX": "",
        "DYNAMODB_TIMEOUT": "30",
    },
    clear=True,
)
def test_status_fails_if_cant_connect_to_db(event):
    with moto.mock_dynamodb():
        from api.consumer.status.index import handler

        assert handler(event=event) == SERVICE_UNAVAILABLE


@moto.mock_dynamodb
@mock.patch.dict(
    os.environ,
    {
        **BASE_FIELDS,
        "AWS_DEFAULT_REGION": "eu-west-2",
        "AWS_REGION": "eu-west-2",
        "PREFIX": "",
        "DYNAMODB_TIMEOUT": "30",
    },
    clear=True,
)
def test_status_ok(event):
    from api.consumer.status.index import DYNAMODB_CLIENT, handler

    for model, config in TABLE_CONFIG.items():
        DYNAMODB_CLIENT.create_table(
            TableName=model.kebab(),
            **config,
        )

    assert handler(event=event) == OK
