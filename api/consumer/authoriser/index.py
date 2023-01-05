import os

from nrlf.core.authoriser import Config, build_persistent_dependencies, execute_steps

config = Config(
    **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
)
dependencies = build_persistent_dependencies(config)


def handler(event, context=None) -> dict[str, str]:

    _, result = execute_steps(
        index_path=__file__, event=event, context=context, config=config, **dependencies
    )

    return result
