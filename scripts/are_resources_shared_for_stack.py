#!/usr/bin/env python
# Get if the stack should share resources
import fire

persistent_environments = [
    "dev-1",
    "dev-2",
    "dev-sandbox-1",
    "dev-sandbox-2",
    "qa-1",
    "qa-2",
    "qa-sandbox-1",
    "qa-sandbox-2",
    "ref-1",
    "ref-2",
    "int-1",
    "int-2",
    "int-sandbox-1",
    "int-sandbox-2",
    "prod-1",
    "prod-2",
]


def uses_shared_resources(stack_name: str) -> bool:
    return stack_name in persistent_environments


def main(stack_name) -> str:
    return "true" if uses_shared_resources(stack_name) else "false"


if __name__ == "__main__":
    fire.Fire(main)
