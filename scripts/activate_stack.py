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
VALID_LOCK_STATES = [STATE_LOCKED, STATE_OPEN]


def _set_lock_state(
    lock_state: str, environment_config: dict, parameters_key: str, sm: any
):
    if lock_state not in VALID_LOCK_STATES:
        raise ValueError(f"Invalid lock state: {lock_state}")

    print(f"Setting environment config lock state to {lock_state}....")
    environment_config[CONFIG_LOCK_STATE] = lock_state
    sm.put_secret_value(
        SecretId=parameters_key, SecretString=json.dumps(environment_config)
    )
    print(f"Environment config lock state is now {lock_state}")


def _update_and_unlock(environment_config: dict, parameters_key: str, sm: any):
    environment_config[CONFIG_LOCK_STATE] = STATE_OPEN

    print(f"Updating environment config to: {environment_config}")
    sm.put_secret_value(
        SecretId=parameters_key, SecretString=json.dumps(environment_config)
    )


def _switch_active_stack(stack_name: str):
    # Change API mappings for APIGW
    print(f"Switching APIGW to point to {stack_name}")
    # TODO


def main(stack_name: str, env: str):
    boto_session = get_boto_session(env)
    sm = boto_session.client("secretsmanager")

    parameters_key = f"nhsd-nrlf--{env}--env-config"
    response = sm.get_secret_value(SecretId=parameters_key)

    environment_config = json.loads(response["SecretString"])
    print(f"Got environment config for ${env}: {environment_config}")

    lock_state = environment_config[CONFIG_LOCK_STATE]
    if lock_state != "open":
        print(
            f"Unable to activate stack as lock state is not open: {lock_state}",
            file=sys.stderr,
        )
        return

    active_stack = environment_config[CONFIG_ACTIVE_STACK]
    if active_stack == stack_name:
        print("Cannot activate stack, stack is already active", file=sys.stderr)
        return

    _set_lock_state(
        STATE_LOCKED,
        environment_config=environment_config,
        parameters_key=parameters_key,
        sm=sm,
    )

    try:
        print(f"Activating stack {stack_name}....")
        _switch_active_stack(stack_name)
    except Exception as err:
        print(
            "Failed to switch active stack. Unlocking and bailing out....",
            file=sys.stderr,
        )
        _set_lock_state(
            STATE_OPEN,
            environment_config=environment_config,
            parameters_key=parameters_key,
            sm=sm,
        )
        print(f"Failed to activate stack: {err}", file=sys.stderr)
        return

    print("Updating environment config and unlocking....")
    environment_config[CONFIG_INACTIVE_STACK] = active_stack
    environment_config[CONFIG_ACTIVE_STACK] = stack_name
    _update_and_unlock(environment_config, parameters_key=parameters_key, sm=sm)

    print(f"Complete. Stack {stack_name} is now the active stack for {env}")


if __name__ == "__main__":
    fire.Fire(main)
