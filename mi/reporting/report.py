from typing import Generator

import fire

from helpers.aws_session import new_session_from_env
from mi.reporting.actions import each_query_event, perform_query, write_csv


def make_reports(
    session, env: str, workspace: str = None, partition_key=None
) -> Generator[tuple[str, str], None, None]:
    if workspace is None:
        workspace = env

    for report_name, event in each_query_event(
        session=session, workspace=workspace, env=env, partition_key=partition_key
    ):
        data = perform_query(session=session, workspace=workspace, event=event)
        out_path = write_csv(
            data=data,
            workspace=workspace,
            env=env,
            report_name=report_name,
            partition_key=partition_key,
        )
        yield report_name, out_path


def _make_reports(env: str, workspace: str = None, partition_key=None):
    session = new_session_from_env(env=env)
    for _ in make_reports(
        session=session, env=env, workspace=workspace, partition_key=partition_key
    ):
        pass


if __name__ == "__main__":
    fire.Fire(_make_reports)
