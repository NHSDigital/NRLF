from enum import Enum

from nrlf.producer.fhir.r4.model import Coding, Meta, ProfileItem

META = Meta(
    profile=[
        ProfileItem(
            __root__="https://fhir.nhs.uk/StructureDefinition/NHSDigital-OperationOutcome"
        )
    ]
)
SPINE_SYSTEM = "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode"
NRLF_SYSTEM = "https://fhir.nhs.uk/CodeSystem/NRLF-SuccessCode"


class IssueType(Enum):
    # https://simplifier.net/packages/hl7.fhir.r4.core/4.0.1/files/83603/~json
    PROCESSING = "processing"
    INFORMATIONAL = "informational"


class IssueSeverity(Enum):
    # https://build.fhir.org/valueset-issue-severity.html
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class SpineCoding(Enum):
    # https://simplifier.net/packages/uk.nhsdigital.r4/2.6.1/files/788913/~json
    ACCESS_DENIED = Coding(
        code="ACCESS_DENIED",
        display="Access has been denied to process this request",
        system=SPINE_SYSTEM,
    )
    ACCESS_DENIED_LEVEL = Coding(
        code="ACCESS_DENIED_LEVEL",
        display="Access has been denied because you need higher level permissions",
        system=SPINE_SYSTEM,
    )
    ACCESS_TOKEN_EXPIRED = Coding(
        code="ACCESS_TOKEN_EXPIRED",
        display="Access token has expired",
        system=SPINE_SYSTEM,
    )
    ACCESS_TOKEN_INVALID = Coding(
        code="ACCESS_TOKEN_INVALID",
        display="Authorization header not formatted correctly",
        system=SPINE_SYSTEM,
    )
    ACCESS_TOKEN_MISSING = Coding(
        code="ACCESS_TOKEN_MISSING",
        display="Authorization header not sent",
        system=SPINE_SYSTEM,
    )
    TIMEOUT = Coding(
        code="TIMEOUT", display="Request has timed out", system=SPINE_SYSTEM
    )
    TOO_MANY_REQUESTS = Coding(
        code="TOO_MANY_REQUESTS",
        display="Your connection has exceeded the rate limit",
        system=SPINE_SYSTEM,
    )
    METHOD_NOT_ALLOWED = Coding(
        code="METHOD_NOT_ALLOWED", display="Method not allowed", system=SPINE_SYSTEM
    )
    SERVICE_UNAVAILABLE = Coding(
        code="SERVICE_UNAVAILABLE",
        display="Service unavailable - could be temporary",
        system=SPINE_SYSTEM,
    )
    SERVICE_ERROR = Coding(
        code="SERVICE_ERROR",
        display="Service failure or unexpected error",
        system=SPINE_SYSTEM,
    )
    RESOURCE_NOT_FOUND = Coding(
        code="RESOURCE_NOT_FOUND", display="Resource not found", system=SPINE_SYSTEM
    )
    MISSING_HEADER = Coding(
        code="MISSING_HEADER",
        display="A required header is missing",
        system=SPINE_SYSTEM,
    )
    VALIDATION_ERROR = Coding(
        code="VALIDATION_ERROR",
        display="A parameter or value has resulted in a validation error",
        system=SPINE_SYSTEM,
    )
    MISSING_VALUE = Coding(
        code="MISSING_VALUE", display="A required value is missing", system=SPINE_SYSTEM
    )
    NOT_ACCEPTABLE = Coding(
        code="NOT_ACCEPTABLE",
        display="Compatible content was not available",
        system=SPINE_SYSTEM,
    )


class NrlfCoding(Enum):
    RESOURCE_CREATED = Coding(
        code="RESOURCE_CREATED",
        display="Resource created",
        system=NRLF_SYSTEM,
    )
    RESOURCE_REMOVED = Coding(
        code="RESOURCE_REMOVED",
        display="Resource removed",
        system=NRLF_SYSTEM,
    )
    RESOURCE_SUPERSEDED = Coding(
        code="RESOURCE_SUPERSEDED",
        display="Resource created and Resource(s) deleted",
        system=NRLF_SYSTEM,
    )
    RESOURCE_UPDATED = Coding(
        code="RESOURCE_UPDATED",
        display="Resource updated",
        system=NRLF_SYSTEM,
    )
