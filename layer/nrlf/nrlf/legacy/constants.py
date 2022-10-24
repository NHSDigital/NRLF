import mimetypes
from typing import Literal

LEGACY_SYSTEM = "LEGACY_SYSTEM"
LEGACY_VERSION = -1
NHS_NUMBER_SYSTEM_URL = "https://fhir.nhs.uk/Id/nhs-number"
UPDATE_DATE_FORMAT = r"%a, %d %b %Y %H:%M:%S GMT"
MIME_TYPES = Literal[tuple(mimetypes.types_map.values())]  # type: ignore
