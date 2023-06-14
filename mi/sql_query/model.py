import json
import os
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Extra, Field, SecretStr


class Status(str, Enum):
    OK = "OK"
    ERROR = "ERROR"


class Outcome(str, Enum):
    OPERATION_SUCCESSFUL = "Operation Successful"


class Sql(BaseModel, extra=Extra.forbid):
    statement: str
    identifiers: Optional[dict] = Field(
        default_factory=dict,
        description=(
            "Resources, e.g. table names, column names "
            "names that you want to parametrise in the statement. "
            "In the 'statement' these should be contained within {}"
        ),
    )
    params: Optional[dict] = Field(
        default_factory=dict,
        description=(
            "Values (e.g. for INSERT) that you want to parametrise in the statement. "
            "In the 'statement' these should be contained within %()s"
        ),
    )


class SqlQueryEvent(BaseModel, extra=Extra.forbid):
    password: SecretStr
    user: SecretStr
    endpoint: Optional[str] = None
    database_name: Optional[str] = None
    sql: Sql
    raise_on_sql_error: Optional[bool] = False
    autocommit: Optional[bool] = False

    def dict(self, *args, **kwargs):
        _dict = super().dict(*args, **kwargs)
        _dict.update(
            user=self.user.get_secret_value(),
            password=self.password.get_secret_value(),
        )
        return _dict

    def json(self):
        _dict = self.dict()
        return json.dumps(_dict)


class Environment(BaseModel):
    POSTGRES_DATABASE_NAME: str
    RDS_CLUSTER_HOST: str
    RDS_CLUSTER_PORT: int

    @classmethod
    def construct(cls) -> "Environment":
        return cls(**os.environ)


class Response(BaseModel):
    status: Status
    outcome: str
    results: list[tuple[object, ...]] = None
