from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, StrictStr, root_validator

from nrlf.core_pipeline.validators import json_loads


class AbstractHeader(BaseModel):
    headers: dict = Field(exclude=True)

    @root_validator(pre=True)
    def _convert_keys_to_lowercase(cls, values):
        headers = {key.lower(): value for key, value in values.items()}
        return {"headers": headers, **headers}


class AcceptHeader(AbstractHeader):
    version: str = Field(regex="^\\d+\\.?\\d*$")

    @root_validator(pre=True)
    def _parse_accept_header(cls, values):
        accept_header = values.get("accept")

        try:
            parts = accept_header.split(";")
            parts = map(str.lower, parts)
            parts = map(str.strip, parts)
            parts = filter(lambda part: "=" in part, parts)
            parts = map(lambda item: map(str.strip, item.split("=")), parts)
        except Exception:
            raise ValueError("Invalid accept header")
        return {**values, **dict(parts)}

    class Config:
        json_loads = json_loads


class LoggingHeader(AbstractHeader):
    correlation_id: Optional[StrictStr] = Field(
        alias="x-correlation-id", default_factory=lambda: str(uuid4())
    )
    nhsd_correlation_id: Optional[StrictStr] = Field(alias="nhsd-correlation-id")
    request_id: Optional[StrictStr] = Field(
        alias="x-request-id", default_factory=lambda: str(uuid4())
    )
