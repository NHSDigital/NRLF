from pydantic import BaseModel, Field, validator


class AcceptHeader(BaseModel):
    parsing_error: str = Field(exclude=True)
    version: str

    def __init__(self, event):
        headers = self._convert_keys_to_lowercase(event.get("headers", {}))
        parsing_error, accept_header = self._parse_accept_header(headers.get("accept"))
        super().__init__(parsing_error=parsing_error, **accept_header)

    @staticmethod
    def _convert_keys_to_lowercase(headers):
        return {key.lower(): value for key, value in headers.items()}

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
