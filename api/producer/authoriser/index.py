import os

import boto3

from nrlf.core.authoriser import Config, build_persistent_dependencies, execute_steps

config = Config(
    **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
)
S3_CLIENT = boto3.client("s3")
dependencies = build_persistent_dependencies(config=config, s3_client=S3_CLIENT)


def handler(event, context=None) -> dict[str, str]:
    _, result = execute_steps(
        index_path=__file__, event=event, context=context, config=config, **dependencies
    )

    return result
