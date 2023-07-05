import itertools
import os
from io import StringIO

import fire
import sh

from helpers.aws_session import _get_access_token, aws_account_id_from_profile

ALLOWED_COMMANDS = {"query", "scan", "get-item", "delete-item"}


class CommandNotAllowed(Exception):
    pass


def dynamodb(command: str, *, env: str, **command_parameters: dict[str, str]):
    account_id = aws_account_id_from_profile(env=env)
    access_key_id, secret_access_key, session_token = _get_access_token(
        account_id=account_id
    )
    session_credentials = {
        "AWS_ACCESS_KEY_ID": access_key_id,
        "AWS_SECRET_ACCESS_KEY": secret_access_key,
        "AWS_SESSION_TOKEN": session_token,
    }

    if command not in ALLOWED_COMMANDS:
        raise CommandNotAllowed(command)

    params = {f"--{k.replace('_', '-')}": v for k, v in command_parameters.items()}
    with StringIO() as buffer:
        try:
            sh.aws(
                "dynamodb",
                command,
                *itertools.chain.from_iterable(params.items()),
                _env={**os.environ, **session_credentials},
                _out=buffer,
            )
        except sh.ErrorReturnCode as exc:
            print(exc.stderr.decode(), end="")  # noqa: T201
        else:
            print(buffer.getvalue())  # noqa: T201


if __name__ == "__main__":
    fire.Fire({"dynamodb": dynamodb})
