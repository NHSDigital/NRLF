from datetime import date, datetime
from pathlib import Path
from typing import Generator

from helpers.log import log
from mi.reporting.paths import PATH_TO_QUERIES

RESOURCE_PREFIX = "nhsd-nrlf"
LAMBDA_NAME = RESOURCE_PREFIX + "--{workspace}--mi--sql_query"
SECRET_NAME = RESOURCE_PREFIX + "--{workspace}--{workspace}--{operation}_password"
DB_CLUSTER_NAME = RESOURCE_PREFIX + "-{env}-aurora-cluster"


@log("Got credentials")
def get_credentials(session, workspace: str, operation: str = "read") -> dict:
    secret_name = SECRET_NAME.format(workspace=workspace, operation=operation)
    client = session.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return {"user": f"{workspace}-{operation}", "password": response["SecretString"]}


@log("Got SQL statement {__result__}")
def each_sql_statement() -> Generator[tuple[str, str], None, None]:
    for path in Path(PATH_TO_QUERIES).iterdir():
        if path.is_dir():
            continue
        report_name = path.stem
        with open(path) as f:
            sql_statement = f.read()
            yield report_name, sql_statement


@log("Got SQL identifiers {__result__}")
def get_sql_identifiers() -> dict:
    return {}


@log("Got endpoint {__result__}")
def get_endpoint(session, env: str, operation: str = "read") -> str:
    client = session.client("rds")
    response = client.describe_db_clusters(
        DBClusterIdentifier=DB_CLUSTER_NAME.format(env=env)
    )
    (cluster,) = response["DBClusters"]
    if operation == "read":
        return cluster["ReaderEndpoint"]
    return cluster["Endpoint"]


@log("Got lambda name {__result__}")
def get_lambda_name(workspace: str) -> str:
    return LAMBDA_NAME.format(workspace=workspace)


@log("Preparing to write results to {__result__}")
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
