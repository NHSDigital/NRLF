import datetime
import json
from datetime import date

from moto import mock_rds, mock_secretsmanager

from mi.reporting.resources import (
    get_credentials,
    get_endpoint,
    get_sql_identifiers,
    get_sql_statement,
)


@mock_secretsmanager
def test_get_credentials():
    import boto3

    _creds = {"user": "foo", "password": "bar"}  # pragma: allowlist secret
    client = boto3.client("secretsmanager")
    client.create_secret(
        Name="nrlf-nhsd-FOO--mi--schema_lambda", SecretString=json.dumps(_creds)
    )
    creds = get_credentials(session=client, workspace="FOO")
    assert creds == _creds


def test_get_sql_statement():
    assert get_sql_statement().startswith("SELECT")


def test_get_sql_identifiers():
    identifiers = get_sql_identifiers(workspace="FOO")
    assert identifiers == {"table_name": "nrlf-nhsd-FOO-mi"}


@mock_rds
def test_get_endpoint():
    import boto3

    client = boto3.client("rds")
    client.create_db_cluster(
        DBClusterIdentifier="nrlf-nhsd-FOO-aurora-cluster",
        Engine="aurora",
        MasterUsername="root",
        MasterUserPassword="pwd",  # pragma: allowlist secret
    )
    assert (
        get_endpoint(session=client, env="FOO")
        == "nrlf-nhsd-FOO-aurora-cluster.cluster-12345678910-ro.eu-west-2.rds.amazonaws.com"
    )


def test_make_report_path():
    assert (
        test_make_report_path(
            path="FOO",
            env="BAR",
            workspace="BAZ",
            today=date(day=1, month=2, year=2000),
            now=datetime(second=30, minute=2, hour=3, day=1, month=2, year=2000),
        )
        == "FOO/2000/2/1/mi-report-BAR-BAZ-1-2-2000:030230"
    )
