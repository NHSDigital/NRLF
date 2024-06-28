#!/usr/bin/env python
import json
import sys

import fire
from aws_session_assume import get_boto_session


def main(parameter_name: str, env: str):
    boto_session = get_boto_session(env)
    ssm = boto_session.client("ssm")

    parameter_key = f"/nhsd-nrlf-{env}/environment-config"
    response = ssm.get_parameter(Name=parameter_key, WithDecryption=True)

    parameters = json.loads(response["Parameter"]["Value"])

    if parameter_name in parameters:
        print(parameters[parameter_name])
    else:
        print(
            f"Parameter {parameter_name} not found in environment config",
            file=sys.stderr,
        )


if __name__ == "__main__":
    fire.Fire(main)
