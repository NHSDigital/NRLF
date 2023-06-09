import csv
import json
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
from mi.schema_lambda.model import Query, QueryEvent, Response, Status


@log("Creating query event")
def make_query_event(session, workspace: str, env: str) -> dict:
    credentials = get_credentials(session=session, workspace=workspace)
    endpoint = get_endpoint(session=session, env=env)
    statement = get_sql_statement()
    identifiers = get_sql_identifiers(workspace=workspace)
    return QueryEvent(
        query=Query(statement=statement, identifiers=identifiers),
        endpoint=endpoint,
        **credentials,
    ).dict()


@log("Querying lambda on {column_names}")
def perform_query(
    session, workspace: str, event: dict, column_names: list[str]
) -> list[dict]:
    function_name = get_lambda_name(workspace=workspace)
    client = session.client("lambda")
    raw_response = client.invoke(FunctionName=function_name, Payload=json.dumps(event))
    response = Response(**raw_response)
    if response.status != Status.OK:
        raise Exception(response.outcome)
    return [dict(zip(column_names, line)) for line in response.results]


@log("Wrote report to {__result__}")
def write_csv(
    data: list[dict],
    env: str,
    workspace: str,
    column_names: list[str],
    path: Path = PATH_TO_REPORT_CSV,
) -> str:
    out_path = make_report_path(path=path, env=env, workspace=workspace)
    with open(out_path, "w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=column_names)
        writer.writeheader()
        for line in data:
            writer.writerow(line)
