from typing import Dict, Tuple

from pydantic import BaseModel, Field, validator
import math

class VersionException(Exception):
    pass

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
    def _parse_accept_header(accept_header: str) -> Tuple[str, Dict[str, str]]:
        if type(accept_header) is not str:
            return "Accept header must be a string", {}

        try:
            parts = accept_header.split(";")
            parts = map(str.lower, parts)
            parts = map(str.strip, parts)
            parts = map(lambda item: map(str.strip, item.split("=")), parts)
            return "", dict(parts)
        except Exception:
            return "Invalid accept header", {}

    @validator("parsing_error")
    def raise_parsing_error(cls, parsing_error):
        if parsing_error:
            raise ValueError(parsing_error)
        return parsing_error


def get_version_from_header(event) -> str:
    accept_header = AcceptHeader(event)
    return accept_header.version


def get_steps(requested_version: str, handler_versions: Dict[str, any]):
    version = get_largest_possible_version(requested_version, handler_versions)
    return handler_versions[version]

def get_largest_possible_version(
    requested_version: str, handler_versions: Dict[str, any]
) -> str:
    all_versions = [int(key) for key in handler_versions]
    possible_versions = [
        version for version in all_versions if int(requested_version) >= version
    ]
    largest_possible_version = max(possible_versions, default=math.inf)
    if not math.isfinite(largest_possible_version):
        raise VersionException("Version not supported")
    return str(largest_possible_version)
