#!/usr/bin/env python
import json
import sys

import fire
from aws_session_assume import get_boto_session


def main(parameter_name: str, parameter_value: str, env: str):
    boto_session = get_boto_session(env)
    sm = boto_session.client("secretsmanager")

    secret_key = f"nhsd-nrlf--{env}--env-config"
    response = sm.get_secret_value(SecretId=secret_key)
    parameters = json.loads(response["SecretString"])

    if parameter_name in parameters:
        current_value = parameters[parameter_name]
        if current_value == parameter_value:
            print(
                f"'{parameter_name}' already set to '{parameter_value}'. No changes made."
            )
            sys.exit(0)

        print(
            f"Updating '{parameter_name}' from '{current_value}' to '{parameter_value}'...."
        )
        parameters[parameter_name] = parameter_value
    else:
        print(f"Adding '{parameter_name}' with value '{parameter_value}'....")
        parameters[parameter_name] = parameter_value

    response = sm.put_secret_value(
        SecretId=secret_key, SecretString=json.dumps(parameters)
    )

    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
        print("Updated successfully")
    else:
        print(f"Update failed with: {response}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    fire.Fire(main)
