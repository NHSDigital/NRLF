from datetime import date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Generator

from helpers.log import log
from mi.reporting.constants import (
    DATE_PATTERN,
    DB_CLUSTER_NAME,
    LAMBDA_NAME,
    PATH_TO_QUERIES,
    SECRET_NAME,
)


class BadDateError(Exception):
    pass


def get_credentials(session, workspace: str, operation: str = "read") -> dict:
    secret_name = SECRET_NAME.format(workspace=workspace, operation=operation)
    client = session.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return {"user": f"{workspace}-{operation}", "password": response["SecretString"]}


def each_report_sql_statement() -> Generator[tuple[str, str], None, None]:
    for path in Path(PATH_TO_QUERIES).iterdir():
        if path.is_dir():
            continue
        report_name = path.stem
        with open(path) as f:
            sql_statement = f.read()
            yield report_name, sql_statement


@log("Got endpoint {__result__}")
def get_rds_endpoint(session, env: str, operation: str = "read") -> str:
    client = session.client("rds")
    response = client.describe_db_clusters(
        DBClusterIdentifier=DB_CLUSTER_NAME.format(env=env)
    )
    (cluster,) = response["DBClusters"]
    if operation == "read":
        return cluster["ReaderEndpoint"]
    return cluster["Endpoint"]


def get_lambda_name(workspace: str) -> str:
    return LAMBDA_NAME.format(workspace=workspace)


def make_report_path(
    path: str,
    env: str,
    workspace: str,
    report_name: str,
    today: date = None,
    now: datetime = None,
    partition_key=None,
) -> str:
    today = date.today() if today is None else today
    now = datetime.now() if now is None else now
    partition_key = "" if partition_key is None else partition_key

    date_path = Path(*today.isoformat().split("-"))
    timestamp = now.isoformat().replace(":", "-")

    report_path = Path(path) / date_path / report_name / env / workspace
    if partition_key:
        report_path = report_path / partition_key
    file_name = f"{report_name}-{env}-{workspace}-{timestamp}.csv"

    report_path.mkdir(parents=True, exist_ok=True)
    return str(report_path / file_name)


@log("Converted key '{key}' to integer '{__result__}'")
def hash_str_to_int(key: str, n_digits=8):
    """https://stackoverflow.com/a/42089311/1571593"""
    return int(sha256(key.encode("utf-8")).hexdigest(), 16) % 10**n_digits


def _parse_date(date_str: str):
    try:
        return datetime.strptime(date_str, DATE_PATTERN)
    except ValueError:
        raise BadDateError(
            f"Provided date '{date_str}' does not conform to pattern '{DATE_PATTERN}'"
        )


def parse_date_range(
    start_date: str = None,
    end_date: str = None,
    default_week_interval: int = 1,
    today: datetime = None,
):
    """
    If start_date and end_date are provided, validate them against the expected DATE_PATTERN
    If start_date is not provided, set to one week ago
    If end_date is not provided, set to one week after start_date
    Therefore the default range is one week to today
    """

    if start_date is None:
        today = datetime.now() if today is None else today
        _start_date = today - timedelta(weeks=default_week_interval)
    else:
        _start_date = _parse_date(start_date)

    if end_date is None:
        _end_date = _start_date + timedelta(weeks=default_week_interval)
    else:
        _end_date = _parse_date(end_date)

    return _start_date.strftime(DATE_PATTERN), _end_date.strftime(DATE_PATTERN)
