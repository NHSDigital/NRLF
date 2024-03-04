import boto3

from nrlf.core.authoriser import Config, build_persistent_dependencies, execute_steps

config = Config()
s3_client = boto3.client("s3")
dependencies = build_persistent_dependencies(config=config, s3_client=s3_client)


def handler(event, context=None) -> dict[str, str]:
    _, result = execute_steps(
        index_path=__file__, event=event, context=context, config=config, **dependencies
    )

    return result
