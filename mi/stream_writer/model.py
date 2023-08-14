import os
from enum import Enum

from pydantic import BaseModel


class Status(str, Enum):
    OK = "OK"
    ERROR = "ERROR"


class Outcome(str, Enum):
    OPERATION_SUCCESSFUL = "Operation Successful"


class Environment(BaseModel):
    POSTGRES_DATABASE_NAME: str
    RDS_CLUSTER_HOST: str
    RDS_CLUSTER_PORT: int
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str

    @classmethod
    def construct(cls) -> "Environment":
        return cls(**os.environ)


class Response(BaseModel):
    status: Status
    outcome: str
    results: list[tuple[object, ...]] = None
