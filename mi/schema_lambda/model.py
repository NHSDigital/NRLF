import os
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Extra, Field, SecretStr


class Status(str, Enum):
    OK = "OK"
    ERROR = "ERROR"


class Outcome(Enum):
    OPERATION_SUCCESSFUL = "Operation Successful"


class Query(BaseModel, extra=Extra.forbid):
    statement: str
    identifiers: dict = Field(default_factory=dict)
    params: dict = Field(default_factory=dict)


class QueryEvent(BaseModel, extra=Extra.forbid):
    password: SecretStr
    user: SecretStr
    query: Query
    endpoint: Optional[str] = None


class Environment(BaseModel):
    RDS_CLUSTER_DATABASE_NAME: str
    RDS_CLUSTER_HOST: str
    RDS_CLUSTER_PORT: int

    @classmethod
    def construct(cls) -> "Environment":
        return cls(**os.environ)


class Response(BaseModel):
    status: Status
    outcome: str
    results: list = None
