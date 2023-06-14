import re
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from moto import mock_rds, mock_secretsmanager

from mi.reporting.resources import (
    get_credentials,
    get_endpoint,
    get_sql_identifiers,
    get_sql_statement,
    make_report_path,
)


@mock_secretsmanager
def test_get_credentials():
    import boto3

    client = boto3.client("secretsmanager")
    client.create_secret(
        Name="nhsd-nrlf--FOO--FOO--bar_password",  # pragma: allowlist secret
        SecretString="BAR",  # pragma: allowlist secret
    )
    creds = get_credentials(session=boto3, workspace="FOO", operation="bar")
    assert creds == {"user": "FOO-bar", "password": "BAR"}  # pragma: allowlist secret


def test_get_sql_statement():
    assert get_sql_statement().startswith("SELECT")


def test_get_sql_identifiers():
    identifiers = get_sql_identifiers()
    assert identifiers == {}


@mock_rds
def test_get_endpoint():
    import boto3

    db_id = "nhsd-nrlf-FOO-aurora-cluster"

    client = boto3.client("rds")
    client.create_db_cluster(
        DBClusterIdentifier=db_id,
        Engine="aurora",
        MasterUsername="root",
        MasterUserPassword="the_password",  # pragma: allowlist secret
    )
    endpoint = get_endpoint(session=boto3, env="FOO")
    assert (
        re.match(
            rf"{db_id}.cluster-ro-(\w{{12}}).eu-west-2.rds.amazonaws.com",
            endpoint,
        )
        is not None
    )


def test_make_report_path():
    with TemporaryDirectory() as path:
        expected = f"{path}/2000/02/01/mi-report-BAR-BAZ-2000-02-01T03-02-30.csv"
        assert (
            make_report_path(
                path=path,
                env="BAR",
                workspace="BAZ",
                today=date(day=1, month=2, year=2000),
                now=datetime(second=30, minute=2, hour=3, day=1, month=2, year=2000),
            )
            == expected
        )
        assert Path(expected).parent.exists()
