import re
from pathlib import Path

_PATH_TO_HERE = Path(__file__).parent
PATH_TO_QUERIES = _PATH_TO_HERE / "queries"

UPPER_LOWER_CASE_BOUNDARY_RE = re.compile("(.)([A-Z][a-z]+)")
UPPER_TO_LOWER_WITH_UNDERSCORE_RE = re.compile("([a-z0-9])([A-Z])")
UNDERSCORE_SUB = r"\1_\2"
TYPE_SEPARATOR = "|"
DocumentPointerPkPrefix = "D#"


class DateTimeFormats:
    DOCUMENT_POINTER_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
    FACT_FORMAT = "%Y-%m-%d %H:%M:%S"
