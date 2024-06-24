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
PERMISSION_ALLOW_ALL_POINTER_TYPES = "allow-all-pointer-types"


PRODUCER_URL_PATH = "/producer/FHIR/R4/DocumentReference"


class PointerTypes(Enum):
    MENTAL_HEALTH_PLAN = "http://snomed.info/sct|736253002"
    EMERGENCY_HEALTHCARE_PLAN = "http://snomed.info/sct|887701000000100"
    EOL_COORDINATION_SUMMARY = "http://snomed.info/sct|861421000000109"
    RESPECT_FORM = "http://snomed.info/sct|1382601000000107"
    NEWS2_CHART = "http://snomed.info/sct|1363501000000100"
    CONTINGENCY_PLAN = "http://snomed.info/sct|325691000000100"
    EOL_CARE_PLAN = "http://snomed.info/sct|736373009"
    LLOYD_GEORGE_FOLDER = "http://snomed.info/sct|16521000000101"

    @staticmethod
    def list():
        return list(map(lambda type: type.value, PointerTypes))


class Categories(Enum):
    CARE_PLAN = "http://snomed.info/sct|734163000"
    OBSERVATIONS = "http://snomed.info/sct|1102421000000108"


TYPE_CATEGORIES = {
    PointerTypes.MENTAL_HEALTH_PLAN.value: Categories.CARE_PLAN.value,
    PointerTypes.EMERGENCY_HEALTHCARE_PLAN.value: Categories.CARE_PLAN.value,
    PointerTypes.EOL_COORDINATION_SUMMARY.value: Categories.CARE_PLAN.value,
    PointerTypes.RESPECT_FORM.value: Categories.CARE_PLAN.value,
    PointerTypes.CONTINGENCY_PLAN.value: Categories.CARE_PLAN.value,
    PointerTypes.EOL_CARE_PLAN.value: Categories.CARE_PLAN.value,
    PointerTypes.LLOYD_GEORGE_FOLDER.value: Categories.CARE_PLAN.value,
    PointerTypes.NEWS2_CHART.value: Categories.OBSERVATIONS.value,
}


SYSTEM_SHORT_IDS = {"http://snomed.info/sct": "SCT"}
