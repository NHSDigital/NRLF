import re
from csv import DictReader

import fire
import yaml

from helpers.aws_session import new_session_from_env
from mi.reporting.actions import each_stored_query_event, perform_query, write_csv
from mi.reporting.constants import VALIDATOR_PATH
from mi.reporting.resources import hash_str_to_int


class ReportValidationError(ValueError):
    pass


def get_validator(report_name: str) -> dict:
    with open(VALIDATOR_PATH / f"{report_name}.yaml") as f:
        validator = {k: re.compile(v) for k, v in yaml.safe_load(f).items()}
    return validator


def validate(validator: dict[str, re.Pattern], results: list[dict], report_name: str):
    for row in results:
        extra_fields = row.keys() - validator.keys()
        if extra_fields:
            raise ReportValidationError(f"Extra fields found in output: {extra_fields}")

        missing_fields = validator.keys() - row.keys()
        if missing_fields:
            raise ReportValidationError(f"Fields missing in output: {missing_fields}")

        for field, regex in validator.items():
            value = row[field]
            if not regex.match(value):
                raise ReportValidationError(
                    f"{report_name}: "
                    f"Failed to validate field '{field}' with "
                    f"value '{value}' with pattern '{regex.pattern}'"
                )


def parse_results(path: str):
    with open(path) as f:
        results = list(DictReader(f=f))
    assert len(results) > 0
    return results


def make_reports(session, env: str, workspace: str = None, partition_key=None):
    if workspace is None:
        workspace = env

    for report_name, event in each_stored_query_event(
        session=session, workspace=workspace, env=env, partition_key=partition_key
    ):
        data = perform_query(session=session, workspace=workspace, event=event)
        report_path = write_csv(
            data=data,
            workspace=workspace,
            env=env,
            report_name=report_name,
            partition_key=partition_key,
        )
        results = parse_results(path=report_path)
        validator = get_validator(report_name=report_name)
        validate(validator=validator, results=results, report_name=report_name)


def _make_reports(env: str, workspace: str = None, partition_key=None):
    if partition_key is not None:
        partition_key = str(hash_str_to_int(key=partition_key))

    session = new_session_from_env(env=env)
    try:
        make_reports(
            session=session, env=env, workspace=workspace, partition_key=partition_key
        )
    except ReportValidationError as err:
        print("\n❗❗❗ Validation error found in the previous report: ")  # noqa: T201
        print(str(err))  # noqa: T201


if __name__ == "__main__":
    fire.Fire(_make_reports)
