#!/usr/bin/env python
import json
import sys

import fire
from aws_session_assume import get_boto_session

CONFIG_LOCK_STATE = "lock-state"
CONFIG_INACTIVE_STACK = "inactive-stack"
CONFIG_ACTIVE_STACK = "active-stack"

STATE_LOCKED = "locked"
STATE_OPEN = "open"


def _switch_active_stack(stack_name: str):
    # Change API mappings for APIGW
    print(f"Switching APIGW to point to ${stack_name}")
    # TODO


def main(stack_name: str, env: str):
    boto_session = get_boto_session(env)
    ssm = boto_session.client("ssm")

    parameters_key = f"/nhsd-nrlf-{env}/environment-config"
    response = ssm.get_parameter(Name=parameters_key, WithDecryption=True)

    environment_config = json.loads(response["Parameter"]["Value"])
    print(f"Got environment config for ${env}: ${environment_config}")

    lock_state = environment_config[CONFIG_LOCK_STATE]
    if lock_state is not "open":
        print(
            f"Unable to activate stack as lock state is not open: ${lock_state}",
            file=sys.stderr,
        )
        return 1

    active_stack = environment_config[CONFIG_ACTIVE_STACK]
    if active_stack == stack_name:
        print(f"Cannot activate stack, stack is already active", file=sys.stderr)
        return 1

    print("Locking environment config state....")
    environment_config[CONFIG_LOCK_STATE] = STATE_LOCKED
    ssm.put_parameter(
        Name=parameters_key,
        Value=json.dumps(environment_config),
        Type="SecureString",
        Overwrite=True,
    )
    print("Locked environment-config state")

    print(f"Activating stack ${stack_name}....")
    # 2 - Do AWS toggle
    _switch_active_stack(stack_name)

    # 3 - Update and unlock environment config
    print(f"Updating environment config and unlocking....")
    environment_config[CONFIG_LOCK_STATE] = STATE_OPEN
    environment_config[CONFIG_INACTIVE_STACK] = active_stack
    environment_config[CONFIG_ACTIVE_STACK] = stack_name
    ssm.put_parameter(
        Name=parameters_key,
        Value=json.dumps(environment_config),
        Type="SecureString",
        Overwrite=True,
    )

    print(f"Complete. Stack ${stack_name} is now the active stack for ${env}")


if __name__ == "__main__":
    fire.Fire(main)
