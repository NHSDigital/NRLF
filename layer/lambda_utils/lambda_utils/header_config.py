from typing import Optional

from pydantic import BaseModel, Field, StrictStr, root_validator

from nrlf.core.validators import json_loads


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


class ClientRpDetailsHeader(AbstractHeader):
    developer_app_name: StrictStr = Field(alias="developer.app.name")
    developer_app_id: StrictStr = Field(alias="developer.app.id")


class ConnectionMetadata(AbstractHeader):
    pointer_types: list[str] = Field(alias="nrl.pointer-types", default_factory=list)
    ods_code: str = Field(alias="nrl.ods-code")
    ods_code_extension: str = Field(alias="nrl.ods-code-extension", default=None)
    nrl_permissions: list[str] = Field(alias="nrl.permissions", default_factory=list)
    enable_authorization_lookup: bool = Field(
        alias="nrl.enable-authorization-lookup", default=False
    )

    @property
    def ods_code_parts(self):
        return tuple(filter(None, (self.ods_code, self.ods_code_extension)))


class LoggingHeader(AbstractHeader):
    correlation_id: Optional[StrictStr] = Field(alias="x-correlation-id")
    nhsd_correlation_id: Optional[StrictStr] = Field(alias="nhsd-correlation-id")
    request_id: Optional[StrictStr] = Field(alias="x-request-id")
