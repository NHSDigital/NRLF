from datetime import date, datetime
from pathlib import Path

from helpers.log import log
from mi.reporting.paths import PATH_TO_REPORT_SQL

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
def get_sql_statement() -> str:
    with open(PATH_TO_REPORT_SQL) as f:
        return f.read()


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
    path: str, env: str, workspace: str, today: date = None, now: datetime = None
) -> str:
    today = date.today() if today is None else today
    now = datetime.now() if now is None else now
    date_path = Path(*today.isoformat().split("-"))
    timestamp = now.isoformat().replace(":", "-")

    report_path = Path(path) / date_path
    file_name = f"mi-report-{env}-{workspace}-{timestamp}.csv"

    report_path.mkdir(parents=True, exist_ok=True)
    return str(report_path / file_name)
