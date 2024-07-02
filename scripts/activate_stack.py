#!/usr/bin/env python
import json
import sys
import traceback

import aws_session_assume
import fire

CONFIG_LOCK_STATE = "lock-state"
CONFIG_INACTIVE_STACK = "inactive-stack"
CONFIG_ACTIVE_STACK = "active-stack"
CONFIG_DOMAIN_NAME = "domain-name"

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


def _switch_active_stack(stack_name: str, env_domain_name: str, session: any):
    # Change API mappings for APIGW
    print(f"Gathering data about APIs for {env_domain_name} for {stack_name}....")
    api_gw = session.client("apigateway")
    env_apis = {
        api["name"]: api["id"]
        for api in api_gw.get_rest_apis(limit=100)["items"]
        if api["name"].startswith(f"nhsd-nrlf--{stack_name}--")
    }

    if len(env_apis) != 2:
        raise ValueError(
            f"Expected 2 APIs for stack {stack_name}, got {env_apis.keys()}"
        )

    api_gwv2 = session.client("apigatewayv2")
    existing_mappings = {
        mapping["ApiMappingKey"]: mapping["ApiMappingId"]
        for mapping in api_gwv2.get_api_mappings(DomainName=env_domain_name)["Items"]
    }

    if len(existing_mappings) != 2:
        raise ValueError(
            f"Expected 2 API mappings for domain {env_domain_name}, got {len(existing_mappings)}"
        )
    if "consumer" not in existing_mappings or "producer" not in existing_mappings:
        raise ValueError(
            f"Expected API mappings for consumer and producer, got {existing_mappings.keys()}"
        )

    print(f"Switching APIGW for {env_domain_name} to point to {stack_name}")
    api_gwv2.update_api_mapping(
        ApiId=env_apis[f"nhsd-nrlf--{stack_name}--consumer"],
        DomainName=env_domain_name,
        ApiMappingId=existing_mappings["consumer"],
        Stage="production",
    )
    api_gwv2.update_api_mapping(
        ApiId=env_apis[f"nhsd-nrlf--{stack_name}--producer"],
        DomainName=env_domain_name,
        ApiMappingId=existing_mappings["producer"],
        Stage="production",
    )


def activate_stack(stack_name: str, env: str, session: any):
    sm = session.client("secretsmanager")

    parameters_key = f"nhsd-nrlf--{env}--env-config"
    response = sm.get_secret_value(SecretId=parameters_key)

    environment_config = json.loads(response["SecretString"])
    print(f"Got environment config for {env}: {environment_config}")

    current_active_stack = environment_config[CONFIG_ACTIVE_STACK]
    if current_active_stack == stack_name:
        print("Cannot activate stack, stack is already active", file=sys.stderr)
        sys.exit(1)

    lock_state = environment_config[CONFIG_LOCK_STATE]
    if lock_state != "open":
        print(
            f"Unable to activate stack as lock state is not open: {lock_state}",
            file=sys.stderr,
        )
        sys.exit(1)

    _set_lock_state(
        STATE_LOCKED,
        environment_config=environment_config,
        parameters_key=parameters_key,
        sm=sm,
    )

    try:
        domain_name = environment_config[CONFIG_DOMAIN_NAME]

        print(f"Activating stack {stack_name} for {domain_name}....")
        _switch_active_stack(stack_name, env_domain_name=domain_name, session=session)
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
        print(f"Stack trace: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)

    print("Updating environment config and unlocking....")
    environment_config[CONFIG_INACTIVE_STACK] = current_active_stack
    environment_config[CONFIG_ACTIVE_STACK] = stack_name
    _update_and_unlock(environment_config, parameters_key=parameters_key, sm=sm)

    print(f"Complete. Stack {stack_name} is now the active stack for {env}")


def main(stack_name: str, env: str):
    boto_session = aws_session_assume.get_boto_session(env)
    activate_stack(stack_name, env=env, session=boto_session)


if __name__ == "__main__":
    fire.Fire(main)
