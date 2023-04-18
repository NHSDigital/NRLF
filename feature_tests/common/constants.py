from enum import Enum, auto

from nrlf.core.model import DocumentPointer

DEFAULT_VERSION = 1.0
STATUS_CODE_200 = 200
DUMMY_METHOD_ARN = "dummy_method_arn"
DEFAULT_AUTHORIZATION = "letmein"
SNOMED_SYSTEM = "http://snomed.info/sct"
DEFAULT_METHOD_ARN = "<resource-arn>"

DOCUMENT_POINTER_TABLE_DEFINITION = {
    "AttributeDefinitions": [
        {"AttributeName": "pk", "AttributeType": "S"},
        {"AttributeName": "sk", "AttributeType": "S"},
        {"AttributeName": "pk_1", "AttributeType": "S"},
        {"AttributeName": "sk_1", "AttributeType": "S"},
        {"AttributeName": "pk_2", "AttributeType": "S"},
        {"AttributeName": "sk_2", "AttributeType": "S"},
    ],
    "KeySchema": [
        {"AttributeName": "pk", "KeyType": "HASH"},
        {"AttributeName": "sk", "KeyType": "HASH"},
    ],
    "GlobalSecondaryIndexes": [
        {
            "IndexName": "idx_gsi_1",
            "KeySchema": [
                {"AttributeName": "pk_1", "KeyType": "HASH"},
                {"AttributeName": "sk_1", "KeyType": "RANGE"},
            ],
            "Projection": {
                "ProjectionType": "ALL",
            },
            "ProvisionedThroughput": {
                "ReadCapacityUnits": 123,
                "WriteCapacityUnits": 123,
            },
        },
        {
            "IndexName": "idx_gsi_2",
            "KeySchema": [
                {"AttributeName": "pk_2", "KeyType": "HASH"},
                {"AttributeName": "sk_2", "KeyType": "RANGE"},
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

ALLOWED_CONSUMER_ORG_IDS = ["RX898"]
ALLOWED_CONSUMERS = ["Yorkshire Ambulance Service"]
ALLOWED_PRODUCER_ORG_IDS = ["8FW23", "V4T0L.YGMMC", "V4T0L.CBH"]
ALLOWED_PRODUCERS = [
    "Aaron Court Mental Health NH",
    "BaRS (EMIS)",
    "BaRS (South Derbyshire Mental Health Unit)",
]
ALLOWED_APPS = ["DataShare"]
ALLOWED_APP_IDS = [
    "z00z-y11y-x22x",
    "a33a-b22b-c11c",
]
