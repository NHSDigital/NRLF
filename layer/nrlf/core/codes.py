from typing import ClassVar

from nrlf.consumer.fhir.r4 import model as consumer_model
from nrlf.producer.fhir.r4 import model as producer_model


class _CodeableConcept(producer_model.CodeableConcept, consumer_model.CodeableConcept):  # type: ignore
    """
    Represents a codeable concept with a mapping of codes to text values.
    """

    _TEXT_MAP: ClassVar[dict[str, str]] = {}
    _SYSTEM: ClassVar[str] = ""

    @classmethod
    def from_code(cls, code: str) -> "_CodeableConcept":
        """
        Creates a CodeableConcept instance from a given code.
        """
        if code not in cls._TEXT_MAP:
            raise ValueError(f"Unknown code: {code}")

        return cls(
            coding=[
                producer_model.Coding(
                    system=cls._SYSTEM,
                    code=code,
                    display=cls._TEXT_MAP[code],
                )
            ]
        )


class NRLResponseConcept(_CodeableConcept):
    _SYSTEM = "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode"
    _TEXT_MAP = {
        "RESOURCE_CREATED": "Resource created",
        "RESOURCE_SUPERSEDED": "Resource created and resource(s) deleted",
        "RESOURCE_UPDATED": "Resource updated",
        "RESOURCE_DELETED": "Resource deleted",
    }


class SpineErrorConcept(_CodeableConcept):
    _SYSTEM = "https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1"
    _TEXT_MAP = {
        "ACCESS DENIED": "Access has been denied to process this request",
        "INVALID_RESOURCE": "Invalid validation of resource",
        "NO_RECORD_FOUND": "No record found",
        "INVALID_NHS_NUMBER": "Invalid NHS number",
        "INVALID_CODE_SYSTEM": "Invalid code system",
        "INTERNAL_SERVER_ERROR": "Unexpected internal server error",
        "BAD_REQUEST": "Bad request",
        "AUTHOR_CREDENTIALS_ERROR": "Author credentials error",
        "DUPLICATE_REJECTED": "Create would lead to creation of a duplicate resource",
        "INVALID_PARAMETER": "Invalid parameter",
        "MESSAGE_NOT_WELL_FORMED": "Message not well formed",
        "MISSING_OR_INVALID_HEADER": "There is a required header missing or invalid",
        "INVALID_IDENTIFIER_SYSTEM": "Invalid identifier system",
        "INVALID_CODE_VALUE": "Invalid code value",
        "INVALID_IDENTIFIER_VALUE": "Invalid identifier value",
    }
