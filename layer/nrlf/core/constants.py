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

PRODUCER_URL_PATH = "/nrl-producer-api/FHIR/R4/DocumentReference"
POINTER_TYPES = {
    "736253002": "Mental Health Crisis Plan",
    "1363501000000100": "Royal College of Physicians NEWS2 (National Early Warning Score 2) chart",
    "1382601000000107": "ReSPECT (Recommended Summary Plan for Emergency Care and Treatment) form",
    "325691000000100": "Contingency plan",
    "736373009": "End of life care plan",
    "861421000000109": "End of Life Care Coordination Summary",
    "887701000000100": "Emergency Health Care Plans",
}
