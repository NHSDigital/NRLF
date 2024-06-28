#!/usr/bin/env python
import json

import fire
from aws_session_assume import get_boto_session


def main(parameter_name: str, parameter_value: str, env: str):
    boto_session = get_boto_session(env)
    ssm = boto_session.client("ssm")

    parameter_key = f"/nhsd-nrlf-{env}/environment-config"

    print(f"Getting environment config from ${parameter_key}...")
    response = ssm.get_parameter(Name=parameter_key, WithDecryption=True)
    parameters = json.loads(response["Parameter"]["Value"])

    print(f"Setting parameter {parameter_name} to {parameter_value}...")
    parameters[parameter_name] = parameter_value

    print("Updating environment config...")
    ssm.put_parameter(
        Name=parameter_key,
        Value=json.dumps(parameters),
        Type="SecureString",
        Overwrite=True,
    )


if __name__ == "__main__":
    fire.Fire(main)
