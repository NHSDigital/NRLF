import os
from src.handler import execute_handler, render_response
from src.config import Config, build_persistent_dependencies


config = Config(
    **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
)
dependencies = build_persistent_dependencies(config)


def handler(event, context):
    status_code, result = execute_handler(event, config, **dependencies)
    return render_response(status_code, result)
