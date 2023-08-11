import time

import pytest

from helpers.aws_session import new_aws_session
from helpers.log import log
from helpers.terraform import get_terraform_json
from mi.reporting.report import make_reports
from mi.reporting.tests.test_data.seed_database import _get_test_data, _seed_database


@log("Using test id (partition key) '{__result__}'")
def generate_test_id() -> int:
    """A uniquish ID for defining the test data"""
    return int(time.time() % 10000) * 100


@pytest.mark.integration
def test_make_report():
    tf_json = get_terraform_json()
    environment = tf_json["account_name"]["value"]
    workspace = tf_json["workspace"]["value"]
    account_id = tf_json["assume_account_id"]["value"]
    session = new_aws_session(account_id=account_id)

    test_id = generate_test_id()
    data = _get_test_data(test_id=test_id)
    _seed_database(
        session=session,
        data=data,
        environment=environment,
        workspace=workspace,
    )

    make_reports(
        session=session,
        env=environment,
        workspace=workspace,
        partition_key=str(test_id),
    )
