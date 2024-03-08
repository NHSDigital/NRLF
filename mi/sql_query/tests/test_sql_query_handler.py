import json
import os
import string
from unittest import mock

from hypothesis import given
from hypothesis.strategies import builds, dictionaries, just, text

from mi.sql_query.model import Environment, Sql, SqlQueryEvent
from nrlf.core_pipeline.validators import json_loads

ASCII = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)

text_strategy = text(alphabet=ASCII)
dict_strategy = dictionaries(keys=text_strategy, values=just("hi"))


@mock.patch("mi.sql_query.index.psycopg2")
@mock.patch("mi.sql_query.index.execute_sql_query", return_value=None)
@given(
    event=builds(
        SqlQueryEvent,
        sql=builds(Sql, identifiers=dict_strategy, params=dict_strategy),
    ),
    environment=builds(
        Environment,
        POSTGRES_DATABASE_NAME=text_strategy,
        RDS_CLUSTER_HOST=text_strategy,
    ),
)
def test_handler_pass(
    event: SqlQueryEvent, environment: Environment, mocked_execute_sql_query, mocked_pg
):
    from mi.sql_query.index import handler

    with mock.patch.dict(
        os.environ, {k: str(v) for k, v in environment.dict().items()}, clear=True
    ):
        response = handler(event=event.dict())

    assert json_loads(json.dumps(response)) == {
        "status": "OK",
        "outcome": "Operation Successful",
    }


@mock.patch("mi.sql_query.index.psycopg2")
@mock.patch("mi.sql_query.index.execute_sql_query")
@given(
    event=builds(
        SqlQueryEvent,
        sql=builds(Sql, identifiers=dict_strategy, params=dict_strategy),
    ),
    environment=builds(
        Environment,
        POSTGRES_DATABASE_NAME=text_strategy,
        RDS_CLUSTER_HOST=text_strategy,
    ),
)
def test_handler_fail(
    event: SqlQueryEvent, environment: Environment, mocked_execute_sql_query, mocked_pg
):
    from mi.sql_query.index import handler

    class MyException(Exception):
        pass

    def _raise(*args, **kwargs):
        raise MyException("raised!")

    mocked_execute_sql_query.side_effect = _raise

    with mock.patch.dict(
        os.environ, {k: str(v) for k, v in environment.dict().items()}, clear=True
    ):
        response = handler(event=event.dict())

    assert json_loads(json.dumps(response)) == {
        "status": "ERROR",
        "outcome": "MyException: raised!",
    }


@mock.patch("mi.sql_query.index.psycopg2")
@given(
    event=builds(
        SqlQueryEvent,
        sql=builds(Sql, identifiers=dict_strategy, params=dict_strategy),
    ),
    environment=builds(
        Environment,
        POSTGRES_DATABASE_NAME=text_strategy,
        RDS_CLUSTER_HOST=text_strategy,
    ),
)
def test_handler_connection_fail(
    event: SqlQueryEvent, environment: Environment, mocked_pg
):
    from mi.sql_query.index import handler

    class MyException(Exception):
        pass

    def _raise(*args, **kwargs):
        raise MyException("raised!")

    mocked_pg.connect.side_effect = _raise

    with mock.patch.dict(
        os.environ, {k: str(v) for k, v in environment.dict().items()}, clear=True
    ):
        response = handler(event=event.dict())

    assert json_loads(json.dumps(response)) == {
        "status": "ERROR",
        "outcome": "MyException: raised!",
    }
