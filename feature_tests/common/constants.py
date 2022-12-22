from enum import Enum, auto

from nrlf.core.model import DocumentPointer

DEFAULT_VERSION = 1.0
STATUS_CODE_200 = 200
DUMMY_METHOD_ARN = "dummy_method_arn"
DEFAULT_AUTHORIZATION = "letmein"
SNOMED_SYSTEM = "https://snomed.info/ict"
DEFAULT_METHOD_ARN = "<resource-arn>"

DOCUMENT_POINTER_TABLE_DEFINITION = {
    "AttributeDefinitions": [
        {"AttributeName": "id", "AttributeType": "S"},
        {"AttributeName": "nhs_number", "AttributeType": "S"},
    ],
    "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
    "GlobalSecondaryIndexes": [
        {
            "IndexName": "idx_nhs_number_by_id",
            "KeySchema": [
                {"AttributeName": "nhs_number", "KeyType": "HASH"},
                {"AttributeName": "id", "KeyType": "RANGE"},
            ],
            "Projection": {
                "ProjectionType": "ALL",
            },
            "ProvisionedThroughput": {
                "ReadCapacityUnits": 123,
                "WriteCapacityUnits": 123,
            },
        },
    ],
    "BillingMode": "PAY_PER_REQUEST",
}

TABLE_CONFIG = {
    DocumentPointer: DOCUMENT_POINTER_TABLE_DEFINITION,
}


class TestMode(Enum):
    INTEGRATION_TEST = auto()
    LOCAL_TEST = auto()


class Action(Enum):
    read = auto()
    search = auto()
    searchPost = auto()
    create = auto()
    delete = auto()
    update = auto()
    authoriser = auto()


class ActorType(Enum):
    Producer = auto()
    Consumer = auto()


class Outcomes(Enum):
    successful = True
    unsuccessful = False


class FhirType(Enum):
    DocumentReference = auto()
    OperationOutcome = auto()


ACTION_ALIASES = {"search by POST for": "searchPost"}

ACTION_SLUG_LOOKUP = {
    Action.read: "DocumentReference",
    Action.search: "DocumentReference",
    Action.searchPost: "DocumentReference/_search",
    Action.create: "DocumentReference",
    Action.delete: "DocumentReference",
    Action.update: "DocumentReference",
}

WITH_WITHOUT_ANY = ["with", "without any"]

ALLOWED_TERMS = [
    "actor",
    "action",
    "actor_type",
    "id",
    "app_name",
    "app_id",
    "template_name",
    "message",
    "count",
    "outcome",
    "a_or_an",
    "fhir_type",
    "with_without_any",
]

ALLOWED_CONSUMERS = ["Yorkshire Ambulance Service"]
ALLOWED_PRODUCERS = ["Aaron Court Mental Health NH"]
ALLOWED_APPS = ["DataShare"]
ALLOWED_APP_IDS = ["z00z-y11y-x22x", "a33a-b22b-c11c"]
ALLOWED_CONSUMER_ORG_IDS = ["RX898"]
ALLOWED_PRODUCER_ORG_IDS = ["8FW23"]
