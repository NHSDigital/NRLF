from datetime import date, datetime
from tempfile import TemporaryDirectory
from unittest import mock

import pytest
from hypothesis import given, settings
from hypothesis.strategies import builds, just, lists, text, tuples

from mi.reporting.actions import (
    _column_names_from_sql_query,
    each_stored_query_event,
    perform_query,
    write_csv,
)
from mi.sql_query.model import Response, Sql, SqlQueryEvent, Status

MOCK_PATH = "mi.reporting.actions.{}"


def mock_patch(function_name: str, **kwargs):
    return mock.patch(MOCK_PATH.format(function_name), **kwargs)


@mock_patch(
    "get_credentials",
    return_value={"user": "foo", "password": "FOO"},  # pragma: allowlist secret
)
@mock_patch("get_rds_endpoint", return_value="endpoint")
@mock_patch("each_report_sql_statement", return_value=[["report", "sql"]])
def test_make_query_event(
    _mock_get_credentials, _mock_get_endpoint, _mock_each_sql_statement
):
    ((report_name, query_event),) = each_stored_query_event(
        session=None, workspace=None, env=None, partition_key="party_key"
    )
    assert report_name == "report"
    assert query_event.dict() == {
        "autocommit": False,
        "database_name": None,
        "endpoint": "endpoint",
        "password": "FOO",  # pragma: allowlist secret
        "raise_on_sql_error": False,
        "sql": {
            "identifiers": {},
            "params": {"partition_key": "party_key"},
            "statement": "sql",
        },
        "user": "foo",
    }


@pytest.mark.parametrize(
    ["query", "column_names"],
    [
        (
            "SELECT foo, bar, boom FROM my_table;",
            ["foo", "bar", "boom"],
        ),
        (
            "SELECT foo AS FOO, bar, boom as BOOM FROM my_table;",
            ["FOO", "bar", "BOOM"],
        ),
        (
            "SELECT MIN(a.b.foo) AS FOO, c.d.bar AS bar, e.f.boom FROM my_table;",
            ["FOO", "bar", "e.f.boom"],
        ),
    ],
)
def test__column_names_from_sql_query(query: str, column_names: list[str]):
    assert _column_names_from_sql_query(query) == column_names


@settings(deadline=None)
@given(
    response=builds(
        Response, status=just(Status.OK), results=lists(tuples(text(), text(), text()))
    ),
    event=builds(
        SqlQueryEvent,
        sql=just(Sql(statement="SELECT first, second, third FROM my_table;")),
    ),
)
def test_perform_query_ok(response: Response, event: SqlQueryEvent):
    session = mock.Mock()
    lambda_response = mock.Mock()
    lambda_response.read.return_value = response.json(exclude_none=True)
    session.client.return_value.invoke.side_effect = lambda FunctionName, Payload: {
        "Payload": lambda_response
    }
    data = perform_query(session=session, workspace="foo", event=event)
    assert data == [
        {"first": item[0], "second": item[1], "third": item[2]}
        for item in response.results
    ]


def test_write_csv():
    with TemporaryDirectory() as path:
        out_path = write_csv(
            data=[{"FOO": "foo", "BAR": "bar"}],
            path=path,
            env="theEnv",
            report_name="theReport",
            workspace="theWorkspace",
            today=date(day=1, month=2, year=2000),
            now=datetime(second=30, minute=2, hour=3, day=1, month=2, year=2000),
        )
        assert (
            out_path
            == f"{path}/2000/02/01/theReport/theEnv/theWorkspace/theReport-theEnv-theWorkspace-2000-02-01T03-02-30.csv"
        )
        with open(out_path) as f:
            data = f.read()

        assert data == '"FOO","BAR"\n"foo","bar"\n'
