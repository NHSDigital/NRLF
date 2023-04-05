from enum import Enum, auto


class Source(Enum):
    NRLF = "NRLF"
    LEGACY = "NRL"


class DbPrefix(Enum):
    DocumentPointer = auto()
    Patient = auto()
    Organization = auto()
    CreatedOn = auto()

    def __str__(self):
        return self.name[0]


VALID_SOURCES = frozenset(item.value for item in Source.__members__.values())
EMPTY_VALUES = ("", None, [], {})
JSON_TYPES = {dict, list}
NHS_NUMBER_INDEX = "idx_nhs_number_by_id"
ID_SEPARATOR = "-"
NHS_NUMBER_SYSTEM_URL = "https://fhir.nhs.uk/Id/nhs-number"
