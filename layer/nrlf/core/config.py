from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    The Config class defines all the Environment Variables that are needed for
    the business logic to execute successfully.
    All Environment Variables are validated using pydantic, and will result in
    a 500 Internal Server Error if validation fails.

    To add a new Environment Variable simply add a new pydantic compatible
    definition below, and pydantic should allow for even complex validation
    logic to be supported.
    """

    AWS_REGION: str = Field(default=...)
    PREFIX: str = Field(default=...)
    ENVIRONMENT: str = Field(default=...)
    SPLUNK_INDEX: str = Field(default=...)
    SOURCE: str = Field(default=...)
    AUTH_STORE: str = Field(default=...)
    TABLE_NAME: str = Field(default=...)
