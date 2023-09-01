import os
from logging import Logger
from types import FunctionType, ModuleType

from lambda_pipeline.types import LambdaContext
from lambda_utils.logging import (
    MinimalEventModelForLogging,
    prepare_default_event_for_logging,
)
from lambda_utils.pipeline import render_response
from lambda_utils.status_endpoint import get_mutable_pipeline

from cron.seed_sandbox.config import Config, build_persistent_dependencies
from cron.seed_sandbox.steps import steps

config = Config(
    **{
        env_var: os.environ.get(env_var)
        for env_var in Config.__fields__.keys()
        if os.environ.get(env_var) is not None
    }
)
dependencies = build_persistent_dependencies(config)


def _patched_execute_steps(
    event: MinimalEventModelForLogging, context: LambdaContext, pipeline: ModuleType
) -> FunctionType:
    """The regular _execute_steps expects an APIGatewayProxyEventModel, so swap out _execute_steps with this patch"""

    def func(*args, logger: Logger, **kwargs) -> dict:
        pipeline_steps = pipeline.make_pipeline(
            steps=steps,
            event=event,
            context=context,
            dependencies=dependencies,
            logger=logger,
        )
        result: pipeline.PipelineData = pipeline_steps(data=pipeline.PipelineData())
        return result.to_dict()

    return func


def _do_nothing(*args, **kwargs) -> None:
    return None


def handler(_event: dict, context: LambdaContext = None) -> dict[str, str]:
    if context is None:
        context = LambdaContext()

    event = prepare_default_event_for_logging()

    with get_mutable_pipeline() as mutable_pipeline:
        mutable_pipeline._get_steps_for_version_header = (
            _do_nothing  # No versions of this lambda
        )
        mutable_pipeline._execute_steps = _patched_execute_steps(
            event=event, context=context, pipeline=mutable_pipeline
        )

        status_code, result = mutable_pipeline.execute_steps(
            index_path=__file__,
            event=event.dict(exclude_none=True),
            context=context,
            **dependencies
        )
        return render_response(status_code, result)
