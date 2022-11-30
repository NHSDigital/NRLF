from enum import Enum


class Source(Enum):
    NRLF = "NRLF"
    LEGACY = "NRL"


VALID_SOURCES = frozenset(item.value for item in Source.__members__.values())
EMPTY_VALUES = ("", None, [], {})
JSON_TYPES = {dict, list}
