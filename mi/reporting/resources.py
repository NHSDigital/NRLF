from datetime import date
from datetime import datetime as dt
from pathlib import Path

from helpers.log import log
from mi.reporting.paths import PATH_TO_REPORT_SQL
from nrlf.core.validators import json_loads

RESOURCE_PREFIX = "nrlf-nhsd"
LAMBDA_NAME = RESOURCE_PREFIX + "-{workspace}--mi--schema_lambda"
SECRET_NAME = RESOURCE_PREFIX + "-{workspace}--read_password"
TABLE_NAME = RESOURCE_PREFIX + "-{workspace}-mi"
DB_CLUSTER_NAME = RESOURCE_PREFIX + "-{env}--aurora-cluster"


@log("Got credentials from {secret_name}")
def get_credentials(session, workspace: str) -> dict:
    secret_name = SECRET_NAME.format(workspace=workspace)
    client = session.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return json_loads(response["SecretString"])


@log("Got SQL statement {__result__}")
def get_sql_statement() -> str:
    with open(PATH_TO_REPORT_SQL) as f:
        return f.read()


@log("Got SQL identifiers {__result__}")
def get_sql_identifiers(workspace: str) -> dict:
    return {"table_name": TABLE_NAME.format(workspace=workspace)}


@log("Got endpoint {__result__}")
def get_endpoint(session, env: str) -> str:
    client = session.client("rds")
    response = client.describe_db_clusters(
        DBClusterIdentifier=DB_CLUSTER_NAME.format(env=env)
    )
    return response["DBClusters"]["ReaderEndpoint"]


@log("Got lambda name {__result__}")
def get_lambda_name(workspace: str) -> str:
    return LAMBDA_NAME.format(workspace=workspace)


@log("Writing result to {__result__}")
def make_report_path(
    path: str, env: str, workspace: str, today: date = None, now: dt = None
):
    today = date.today() if today is None else today
    now = dt.now() if now is None else now
    date_path = Path(*today.isoformat().split("-"))
    timestamp = now.isoformat()
    return str(Path(path) / date_path / f"mi-report-{env}-{workspace}-{timestamp}.csv")
