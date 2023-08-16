import json
import os
import string
from unittest import mock

from aws_lambda_powertools.utilities.parser.models import (
    DynamoDBStreamChangedRecordModel,
    DynamoDBStreamModel,
    DynamoDBStreamRecordModel,
)
from hypothesis import given
from hypothesis.strategies import builds, dictionaries, just, lists, text

from mi.stream_writer.model import Environment
from nrlf.core.validators import json_loads

ASCII = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)

text_strategy = text(alphabet=ASCII, min_size=1)
dict_strategy = dictionaries(keys=text_strategy, values=just("hi"))
image_strategy = just({"custodian": {"S": "RJ11"}})
keys_stategy = just({"sk": {"S": "D#RJ11#5"}})


@mock.patch("mi.stream_writer.index.boto3")
@mock.patch("mi.stream_writer.index.psycopg2")
@given(
    event=builds(
        DynamoDBStreamModel,
        Records=lists(
            builds(
                DynamoDBStreamRecordModel,
                dynamodb=builds(
                    DynamoDBStreamChangedRecordModel,
                    NewImage=image_strategy,
                    OldImage=image_strategy,
                    Keys=keys_stategy,
                ),
            )
        ),
    ),
    environment=builds(
        Environment,
        POSTGRES_DATABASE_NAME=text_strategy,
        RDS_CLUSTER_HOST=text_strategy,
        POSTGRES_PASSWORD=text_strategy,
        POSTGRES_USERNAME=text_strategy,
    ),
)
def test_handler_connection_fail(
    event: DynamoDBStreamModel, environment: Environment, mocked_pg, mocked_boto3
):
    from mi.stream_writer.index import handler

    class MyException(Exception):
        pass

    def _raise(*args, **kwargs):
        raise MyException("raised!")

    mocked_pg.connect.side_effect = _raise
    mocked_boto3.client.return_value.get_secret_value.return_value = {
        "SecretId": "oogly"  # pragma: allowlist secret
    }

    with mock.patch.dict(
        os.environ, {k: str(v) for k, v in environment.dict().items()}, clear=True
    ):
        response = handler(event=event.dict())

    assert json_loads(json.dumps(response)) == {
        "status": "ERROR",
        "outcome": "MyException: raised!",
    }
