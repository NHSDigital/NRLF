import json

from aws_lambda_powertools.utilities.parser.models import APIGatewayProxyEventModel
from lambda_utils.logging_utils import generate_transaction_id
from pydantic import BaseModel, Field, StrictStr, validator


class AbstractHeader(BaseModel):
    @staticmethod
    def _convert_keys_to_lowercase(headers):
        return {key.lower(): value for key, value in headers.items()}


class AcceptHeader(AbstractHeader):
    parsing_error: str = Field(exclude=True)
    version: str = Field(regex="^\\d+\\.?\\d*$")

    def __init__(self, event):
        headers = self._convert_keys_to_lowercase(event.get("headers", {}))
        parsing_error, accept_header = self._parse_accept_header(headers.get("accept"))
        super().__init__(parsing_error=parsing_error, **accept_header)

    @staticmethod
    def _parse_accept_header(accept_header: str) -> tuple[str, dict[str, str]]:
        if type(accept_header) is not str:
            return "Accept header must be a string", {}

        try:
            parts = accept_header.split(";")
            parts = map(str.lower, parts)
            parts = map(str.strip, parts)
            parts = filter(lambda part: "=" in part, parts)
            parts = map(lambda item: map(str.strip, item.split("=")), parts)
            return "", dict(parts)
        except Exception:
            return "Invalid accept header", {}

    @validator("parsing_error")
    def raise_parsing_error(cls, parsing_error):
        if parsing_error:
            raise ValueError(parsing_error)
        return parsing_error


class ClientRpDetailsHeader(AbstractHeader):
    custodian: StrictStr = Field(alias="app.ASID")
    pointer_types: list[StrictStr] = Field(alias="nrl.pointer-types")

    def __init__(self, event: APIGatewayProxyEventModel):
        headers = {k.lower(): v for k, v in event.headers.items()}
        client_rp_details = headers.get("nhsd-client-rp-details", "{}")
        super().__init__(**json.loads(client_rp_details))


class LoggingHeader(AbstractHeader):
    correlation_id: StrictStr = Field(alias="x-correlation-id")
    nhsd_correlation_id: StrictStr = Field(alias="nhsd-correlation-id")
    transaction_id: StrictStr = Field(default_factory=generate_transaction_id)
    request_id: StrictStr = Field(alias="x-request-id")
