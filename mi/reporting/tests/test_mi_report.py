import re
from csv import DictReader
from datetime import datetime

import pytest
import yaml

from helpers.aws_session import new_aws_session
from helpers.log import log
from helpers.terraform import get_terraform_json
from mi.reporting.constants import VALIDATOR_PATH
from mi.reporting.report import make_reports
from mi.reporting.tests.test_data.seed_database import _get_test_data, _seed_database


@log("Using test id (partition key) '{__result__}'")
def generate_test_id():
    now = datetime.now()
    return f"TEST-{now.strftime('%Y-%m-%d_%H:%M:%S')}"


def get_validator(report_name: str):
    with open(VALIDATOR_PATH / f"{report_name}.yaml") as f:
        validator = {k: re.compile(v) for k, v in yaml.safe_load(f).items()}
    return validator


def parse_results(path: str):
    with open(path) as f:
        results = list(DictReader(f=f))
    assert len(results) > 0
    return results


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

    for report_name, report_path in make_reports(
        session=session, env=environment, workspace=workspace, partition_key=test_id
    ):
        results = parse_results(path=report_path)
        validator = get_validator(report_name=report_name)

        for row in results:
            extra_fields = row.keys() - validator.keys()
            assert not extra_fields, f"Extra fields found in output: {extra_fields}"

            missing_fields = validator.keys() - row.keys()
            assert not missing_fields, f"Fields missing in output: {missing_fields}"

            for field, regex in validator.items():
                value = row[field]
                assert regex.match(value), (
                    f"Failed to validate field '{field}' with "
                    f"value '{value}' with pattern '{regex.pattern}'"
                )
