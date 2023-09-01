import csv
from datetime import date, datetime
from pathlib import Path
from typing import Generator

from pydantic import ValidationError

from helpers.log import log
from mi.reporting.constants import (
    PATH_TO_REPORT_CSV,
    SQL_ALIAS_SEPARATOR_REGEX,
    SQL_FUNCTION_PARAMS_REGEX,
    SQL_SELECT_REGEX,
    SQL_SELECT_SEPARATOR,
)
from mi.reporting.resources import (
    each_report_sql_statement,
    get_credentials,
    get_lambda_name,
    get_rds_endpoint,
    make_report_path,
)
from mi.sql_query.model import Response, Sql, SqlQueryEvent, Status


@log("Created query events")
def each_stored_query_event(
    session,
    workspace: str,
    env: str,
    partition_key: str,
    start_date: str,
    end_date: str,
) -> Generator[tuple[str, SqlQueryEvent], None, None]:
    credentials = get_credentials(session=session, workspace=workspace)
    endpoint = get_rds_endpoint(session=session, env=env)
    for report_name, statement in each_report_sql_statement():
        yield report_name, SqlQueryEvent(
            sql=Sql(
                statement=statement,
                params={
                    "partition_key": partition_key,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            ),
            endpoint=endpoint,
            **credentials,
        )


def _select_statement_from_sql_query(query: str) -> str:
    try:
        (select,) = SQL_SELECT_REGEX.match(query).groups()
    except:
        raise ValueError(f"Couldn't find valid SELECT statement in query {query}")
    return select


def _column_name_from_statement(column_statement: str) -> str:
    """column_statement ~ 'foo' or 'foo as FOO' or 'foo AS FOO' --> 'foo'"""
    parts = SQL_ALIAS_SEPARATOR_REGEX.split(column_statement)
    last_part = parts[-1]
    return last_part.strip()


def _column_names_from_sql_query(query: str):
    select = _select_statement_from_sql_query(query=query)
    _select = SQL_FUNCTION_PARAMS_REGEX.sub(string=select, repl="")
    column_names = list(
        map(_column_name_from_statement, _select.split(SQL_SELECT_SEPARATOR))
    )
    return column_names


def perform_query(
    session, workspace: str, event: SqlQueryEvent
) -> list[dict[str, any]]:
    function_name = get_lambda_name(workspace=workspace)
    client = session.client("lambda")
    column_names = _column_names_from_sql_query(query=event.sql.statement)
    raw_response = client.invoke(FunctionName=function_name, Payload=event.json())
    _raw_response = raw_response["Payload"].read()
    try:
        response = Response.parse_raw(_raw_response)
    except ValidationError:
        raise Exception(_raw_response)
    if response.status != Status.OK:
        raise Exception(
            f"\nSQL event:\n\n{event}\n\ngot response:\n\n{response.outcome}"
        )
    return [dict(zip(column_names, line)) for line in response.results]


def _get_column_names(data: list[dict]) -> list[str]:
    for row in data:
        return list(row.keys())
    return []


@log("Wrote report to {__result__}")
def write_csv(
    data: list[dict],
    env: str,
    workspace: str,
    report_name: str,
    path: Path = PATH_TO_REPORT_CSV,  # for dependency-injection in unit testing
    today: date = None,  # for dependency-injection in unit testing
    now: datetime = None,  # for dependency-injection in unit testing
    partition_key: str = None,
) -> str:
    today = date.today() if today is None else today
    now = datetime.now() if now is None else now

    out_path = make_report_path(
        path=path,
        env=env,
        workspace=workspace,
        report_name=report_name,
        today=today,
        now=now,
        partition_key=partition_key,
    )
    column_names = _get_column_names(data=data)
    with open(out_path, "w") as csv_file:
        writer = csv.DictWriter(
            csv_file, fieldnames=column_names, quoting=csv.QUOTE_NONNUMERIC
        )
        writer.writeheader()
        for line in data:
            writer.writerow(line)
    return out_path
