import os

from api.producer.deleteDocumentReference.src.config import (
    Config,
    build_persistent_dependencies,
)
from lambda_pipeline.types import LambdaContext
from lambda_utils.pipeline import execute_steps, render_response

config = Config(
    **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
)
dependencies = build_persistent_dependencies(config)


def handler(event: dict, context: LambdaContext = None) -> dict[str, str]:
    if context is None:
        context = LambdaContext()

    status_code, result = execute_steps(
        index_path=__file__, event=event, context=context, config=config, **dependencies
    )
    return render_response(status_code, result)
