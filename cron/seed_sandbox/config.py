import boto3
from pydantic import BaseModel

from cron.seed_sandbox.repository import SandboxRepository


class Config(BaseModel):
    AWS_REGION: str
    PREFIX: str
    ENVIRONMENT: str
    SPLUNK_INDEX: str
    SOURCE: str


def build_persistent_dependencies(config: Config) -> dict[str, any]:
    dynamodb_client = boto3.client("dynamodb")
    return {
        "repository_factory": SandboxRepository.factory(
            client=dynamodb_client, environment_prefix=config.PREFIX
        ),
        "prefix": config.PREFIX,
        "environment": config.ENVIRONMENT,
        "splunk_index": config.SPLUNK_INDEX,
        "source": config.SOURCE,
    }
