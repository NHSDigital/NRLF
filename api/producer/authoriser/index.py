import os

from lambda_pipeline.types import LambdaContext
from lambda_utils.pipeline import execute_steps

from api.producer.authoriser.src.config import Config, build_persistent_dependencies

config = Config(
    **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
)
dependencies = build_persistent_dependencies(config)


def handler(event: dict, context: LambdaContext = None) -> dict[str, str]:
    if context is None:
        context = LambdaContext()

    # This field isnt in the event for authoriser requests for some reason
    # adding it here to pass pydantic validation later
    event["isBase64Encoded"] = False

    _, result = execute_steps(
        index_path=__file__,
        event=event,
        context=context,
        config=config,
        initial_pipeline_data={"method_arn": event["methodArn"]},
        **dependencies
    )

    return result
