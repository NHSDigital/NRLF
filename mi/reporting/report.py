import fire

from helpers.aws_session import new_session_from_env
from mi.reporting.actions import make_query_event, perform_query, write_csv


def make_report(env: str, workspace: str = None):
    if workspace is None:
        workspace = env

    session = new_session_from_env(env=env)
    event = make_query_event(session=session, workspace=workspace, env=env)
    data = perform_query(session=session, workspace=workspace, event=event)
    write_csv(data=data, workspace=workspace, env=env)


if __name__ == "__main__":
    fire.Fire(make_report)
