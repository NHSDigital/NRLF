import re
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from moto import mock_rds, mock_secretsmanager

from mi.reporting.resources import (
    BadDateError,
    each_report_sql_statement,
    get_credentials,
    get_rds_endpoint,
    make_report_path,
    parse_date_range,
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
    for _, sql in each_report_sql_statement():
        assert sql.startswith("SELECT")


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
    endpoint = get_rds_endpoint(session=boto3, env="FOO")
    assert (
        re.match(
            rf"{db_id}.cluster-ro-(\w{{12}}).eu-west-2.rds.amazonaws.com",
            endpoint,
        )
        is not None
    )


def test_make_report_path():
    with TemporaryDirectory() as path:
        expected = f"{path}/2000/02/01/reportName/BAR/BAZ/reportName-BAR-BAZ-2000-02-01T03-02-30.csv"
        assert (
            make_report_path(
                path=path,
                env="BAR",
                workspace="BAZ",
                report_name="reportName",
                today=date(day=1, month=2, year=2000),
                now=datetime(second=30, minute=2, hour=3, day=1, month=2, year=2000),
            )
            == expected
        )
        assert Path(expected).parent.exists()


def test_parse_date_range_check_injection_defaults():
    today = datetime.now()
    default_week_interval = 1
    assert parse_date_range() == parse_date_range(
        today=today, default_week_interval=default_week_interval
    )


def test_parse_date_range_default():
    today = datetime(year=1000, month=1, day=23)
    assert parse_date_range(today=today) == ("1000-01-16", "1000-01-23")


def test_parse_date_range_validation():
    date_range = dict(start_date="1234-01-16", end_date="1234-01-20")
    assert parse_date_range(**date_range) == tuple(date_range.values())


def test_parse_date_range_validation_fails_start_date():
    date_range = dict(start_date="12340116", end_date="1234-01-20")
    with pytest.raises(BadDateError):
        assert parse_date_range(**date_range)


def test_parse_date_range_validation_fails_end_date():
    date_range = dict(start_date="1234-01-16", end_date="12340116")
    with pytest.raises(BadDateError):
        assert parse_date_range(**date_range)
