from lambda_utils.aws import boto3_client
from nrlf.core.model import DocumentPointer
from nrlf.core.repository import Repository
from pydantic import BaseModel


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
    PREFIX: str
    ENVIRONMENT: str


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
    return {
        "repository": Repository(
            item_type=DocumentPointer,
            client=boto3_client("dynamodb"),
            environment_prefix=config.PREFIX,
        ),
        "environment": config.ENVIRONMENT,
    }
