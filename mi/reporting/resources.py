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


def _validate_or_create_date(date_str: str, week_window: int, from_date: date = None):
    if from_date is None:
        from_date = date.today()

    if date_str is None:
        date_str = (from_date - timedelta(weeks=week_window)).strftime(r"%Y-%m-%d")
    try:
        datetime.strptime(date_str, r"%Y-%m-%d")
    except ValueError:
        raise BadDateError(
            f"Provided date '{date_str}' does not conform to pattern '{DATE_PATTERN}'"
        )
    return date_str


def validate_or_create_start_date(start_date: str) -> date:
    return _validate_or_create_date(date_str=start_date, week_window=1)


def validate_or_create_end_date(start_date: str, end_date: str) -> date:
    start_date = datetime.strptime(start_date, r"%Y-%m-%d")
    return _validate_or_create_date(
        date_str=end_date, week_window=0, from_date=start_date
    )
