import boto3
from pydantic import BaseModel

from api.producer.createDocumentReference.src.constants import PersistentDependencies
from nrlf.core.json_schema import JsonSchemaValidatorCache
from nrlf.core.model import Contract, DocumentPointer
from nrlf.core.repository import Repository


class Config(BaseModel):
    """
    The Config class defines all the Environment Variables that are needed for
    the business logic to execute successfully.
    All Environment Variables are validated using pydantic, and will result in
    a 500 Internal Server Error if validation fails.

    To add a new Environment Variable simply a new pydantic compatible
    definition below, and pydantic should allow for even complex validation
    logic to be supported.
    """

    AWS_REGION: str
    DOCUMENT_POINTER_TABLE_NAME: str
    PREFIX: str
    ENVIRONMENT: str
    SPLUNK_INDEX: str
    SOURCE: str


def build_persistent_dependencies(config: Config) -> dict[str, any]:
    """
    AWS Lambdas may be re-used, rather than spinning up a new instance each
    time.  Doing this we can take advantage of state that persists between
    executions.  Any dependencies returned by this function will persist
    between executions and can therefore lead to performance gains.
    This function will be called ONCE in the lambdas lifecycle, which may or
    may not be each execution, depending on how busy the API is.
    These dependencies will be passed through to your `handle` function below.
    """
    dynamo_client = boto3.client("dynamodb")
    return {
        PersistentDependencies.DOCUMENT_POINTER_REPOSITORY: Repository(
            DocumentPointer, dynamo_client, environment_prefix=config.PREFIX
        ),
        "contract_repository": Repository(
            Contract, dynamo_client, environment_prefix=config.PREFIX
        ),
        "json_schema_validator_cache": JsonSchemaValidatorCache(),
        "environment": config.ENVIRONMENT,
        "splunk_index": config.SPLUNK_INDEX,
        "source": config.SOURCE,
    }
