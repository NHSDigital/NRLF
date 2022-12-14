import os

from lambda_pipeline.types import LambdaContext
from lambda_utils import pipeline
from lambda_utils.logging import prepare_default_event_for_logging

from cron.seed_sandbox.config import Config, build_persistent_dependencies
from cron.seed_sandbox.steps import steps

config = Config(
    **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
)
dependencies = build_persistent_dependencies(config)


def handler(event: dict, context: LambdaContext = None) -> dict[str, str]:
    if context is None:
        context = LambdaContext()

    _event = prepare_default_event_for_logging()
    _event.is_default_event = False
    pipeline._get_steps_for_version_header = lambda *args, **kwargs: None
    pipeline._execute_steps = lambda *args, logger, **kwargs: pipeline.make_pipeline(
        steps=steps,
        event=_event,
        context=context,
        dependencies=dependencies,
        logger=logger,
    )(data=pipeline.PipelineData()).to_dict()

    status_code, result = pipeline.execute_steps(
        index_path=__file__,
        event=_event.dict(exclude_none=True),
        context=context,
        config=config,
        **dependencies
    )
    return pipeline.render_response(status_code, result)
