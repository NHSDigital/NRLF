#!/usr/bin/env python
import json
import sys

import fire
from aws_session_assume import get_boto_session


def main(parameter_name: str, env: str):
    boto_session = get_boto_session(env)
    sm = boto_session.client("secretsmanager")

    secret_key = f"nhsd-nrlf--{env}--env-config"
    response = sm.get_secret_value(SecretId=secret_key)
    parameters = json.loads(response["SecretString"])

    if parameter_name in parameters:
        print(parameters[parameter_name])
    else:
        print(
            f"Parameter {parameter_name} not found in environment config",
            file=sys.stderr,
        )


if __name__ == "__main__":
    fire.Fire(main)
