import json
import os
import string
from unittest import mock

from hypothesis import given
from hypothesis.strategies import builds, text

from mi.schema_lambda.model import Environment, QueryEvent
from nrlf.core.validators import json_loads

ASCII = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)


@mock.patch("mi.schema_lambda.handler.psycopg2")
@given(
    event=builds(QueryEvent),
    environment=builds(
        Environment,
        RDS_CLUSTER_DATABASE_NAME=text(alphabet=ASCII),
        RDS_CLUSTER_HOST=text(alphabet=ASCII),
    ),
)
def test_handler_pass(event: QueryEvent, environment: Environment, mocked_pg):
    from mi.schema_lambda.handler import handler

    with mock.patch.dict(
        os.environ, {k: str(v) for k, v in environment.dict().items()}, clear=True
    ):
        response = handler(event=event.dict())

    assert json_loads(json.dumps(response)) == {
        "status": "OK",
        "outcome": "Operation Successful",
    }


@mock.patch("mi.schema_lambda.handler.psycopg2")
@given(
    event=builds(QueryEvent),
    environment=builds(
        Environment,
        RDS_CLUSTER_DATABASE_NAME=text(alphabet=ASCII),
        RDS_CLUSTER_HOST=text(alphabet=ASCII),
    ),
)
def test_handler_fail(event: QueryEvent, environment: Environment, mocked_pg):
    from mi.schema_lambda.handler import handler

    class MyException(Exception):
        pass

    def _raise(*args, **kwargs):
        raise MyException("raised!")

    mocked_pg.connect().cursor().execute.side_effect = _raise

    with mock.patch.dict(
        os.environ, {k: str(v) for k, v in environment.dict().items()}, clear=True
    ):
        response = handler(event=event.dict())

    assert json_loads(json.dumps(response)) == {
        "status": "ERROR",
        "outcome": "MyException: raised!",
    }
