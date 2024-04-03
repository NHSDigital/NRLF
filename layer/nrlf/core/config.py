from pydantic.v1 import BaseSettings, Field


class Config(BaseSettings):
    """
    The Config class defines all the Environment Variables that are needed for
    the business logic to execute successfully.
    All Environment Variables are validated using pydantic, and will result in
    a 500 Internal Server Error if validation fails.

    To add a new Environment Variable simply a new pydantic compatible
    definition below, and pydantic should allow for even complex validation
    logic to be supported.
    """

    AWS_REGION: str = Field(default=..., env="AWS_REGION")
    PREFIX: str = Field(default=..., env="PREFIX")
    ENVIRONMENT: str = Field(default=..., env="ENVIRONMENT")
    SPLUNK_INDEX: str = Field(default=..., env="SPLUNK_INDEX")
    SOURCE: str = Field(default=..., env="SOURCE")
    AUTH_STORE: str = Field(default=..., env="AUTH_STORE")
    FHIRGUARD_METADATA_PATH: str = Field(
        default="/opt/fhirguard-metadata", env="FHIRGUARD_METADATA_PATH"
    )
