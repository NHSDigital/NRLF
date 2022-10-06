from ..config import Config


def handler(event, config: Config, **dependencies):
    return 200, {"message": "version one"}
