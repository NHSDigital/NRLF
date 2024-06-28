#!/usr/bin/env python
import json

import fire
from aws_session_assume import get_boto_session

VALID_PARAMS = ["lock-state", "inactive-stack", "active-stack"]

VALID_LOCK_STATES = ["locked", "open"]


def _validate_parameter(parameter_name: str, parameter_value: str):
    if parameter_name not in VALID_PARAMS:
        raise ValueError(f"Invalid parameter: {parameter_name}")

    if parameter_name == "lock-state" and parameter_value not in VALID_LOCK_STATES:
        raise ValueError(f"Invalid lock state: {parameter_value}")


def main(parameter_name: str, parameter_value: str, env: str):
    _validate_parameter(parameter_name, parameter_value)

    boto_session = get_boto_session(env)
    sm = boto_session.client("secretsmanager")

    secret_key = f"nhsd-nrlf--{env}--env-config"

    print(f"Getting environment config from secret ${secret_key}...")

    response = sm.get_secret_value(SecretId=secret_key)
    parameters = json.loads(response["SecretString"])

    print(f"Setting parameter {parameter_name} to {parameter_value}...")
    parameters[parameter_name] = parameter_value

    print("Updating environment config...")
    sm.put_secret_value(SecretId=secret_key, SecretString=json.dumps(parameters))
    # print(f"Would have updated to: {parameters}")
    print("Environment config updated.")


if __name__ == "__main__":
    fire.Fire(main)
