import csv
import re
from datetime import date, datetime
from pathlib import Path

from helpers.log import log
from mi.reporting.paths import PATH_TO_REPORT_CSV
from mi.reporting.resources import (
    get_credentials,
    get_endpoint,
    get_lambda_name,
    get_sql_identifiers,
    get_sql_statement,
    make_report_path,
)
from mi.sql_query.model import Response, Sql, SqlQueryEvent, Status

SQL_COLUMN_REGEX = re.compile(
    r"(?:\s+as\s+)(\w+)|(?:\s+)(\w+)(?:\,)|(?:\s+)(\w+)(?: from)"
)


@log("Creating query event")
def make_query_event(session, workspace: str, env: str) -> dict:
    credentials = get_credentials(session=session, workspace=workspace)
    endpoint = get_endpoint(session=session, env=env)
    statement = get_sql_statement()
    identifiers = get_sql_identifiers()
    return SqlQueryEvent(
        sql=Sql(statement=statement, identifiers=identifiers),
        endpoint=endpoint,
        **credentials,
    )


def _column_names_from_sql_query(query: str):
    column_names = []
    for result in SQL_COLUMN_REGEX.finditer(query):
        (column_name,) = filter(bool, result.groups())
        column_names.append(column_name)
    return column_names


@log("Querying lambda")
def perform_query(session, workspace: str, event: SqlQueryEvent) -> list[dict]:
    function_name = get_lambda_name(workspace=workspace)
    client = session.client("lambda")
    column_names = _column_names_from_sql_query(query=event.sql.statement)
    raw_response = client.invoke(FunctionName=function_name, Payload=event.json())
    response = Response.parse_raw(raw_response["Payload"].read())
    if response.status != Status.OK:
        raise Exception(response.outcome)
    # NEED TO CORRECTLY COERCE VALUES HERE
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
    path: Path = PATH_TO_REPORT_CSV,
    today: date = None,
    now: datetime = None,
) -> str:
    today = date.today() if today is None else today
    now = datetime.now() if now is None else now

    out_path = make_report_path(
        path=path, env=env, workspace=workspace, today=today, now=now
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
