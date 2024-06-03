from enum import Enum


class Source(Enum):
    NRLF = "NRLF"
    LEGACY = "NRL"


VALID_SOURCES = frozenset(item.value for item in Source.__members__.values())
EMPTY_VALUES = ("", None, [], {})
REQUIRED_CREATE_FIELDS = ["custodian", "id", "type", "status", "subject", "category"]
CATEGORIES = {"734163000": "Care plan", "1102421000000108": "Observations"}
JSON_TYPES = {dict, list}
NHS_NUMBER_INDEX = "idx_nhs_number_by_id"
ID_SEPARATOR = "-"
CUSTODIAN_SEPARATOR = "."
TYPE_SEPARATOR = "|"
KEY_SEPARATOR = "#"
ODS_SYSTEM = "https://fhir.nhs.uk/Id/ods-organization-code"
NHS_NUMBER_SYSTEM_URL = "https://fhir.nhs.uk/Id/nhs-number"
RELATES_TO_REPLACES = "replaces"
ALLOWED_RELATES_TO_CODES = {
    RELATES_TO_REPLACES,
    "transforms",
    "signs",
    "appends",
    "incorporates",
    "summarizes",
}
CLIENT_RP_DETAILS = "nhsd-client-rp-details"
CONNECTION_METADATA = "nhsd-connection-metadata"
PERMISSION_AUDIT_DATES_FROM_PAYLOAD = "audit-dates-from-payload"
PERMISSION_SUPERSEDE_IGNORE_DELETE_FAIL = "supersede-ignore-delete-fail"

PRODUCER_URL_PATH = "/producer/FHIR/R4/DocumentReference"
