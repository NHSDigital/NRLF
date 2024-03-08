from nrlf.consumer.fhir.r4 import model as consumer_model
from nrlf.producer.fhir.r4 import model as producer_model


class NRLResponseConcept(
    producer_model.CodeableConcept, consumer_model.CodeableConcept
):
    _TEXT_MAP = {
        "RESOURCE_CREATED": "Resource created",
        "RESOURCE_SUPERSEDED": "Resource created and resource(s) deleted",
        "RESOURCE_UPDATED": "Resource updated",
        "RESOURCE_DELETED": "Resource deleted",
    }

    @classmethod
    def from_code(cls, error_code: str) -> "NRLResponseConcept":
        if error_code not in cls._TEXT_MAP:
            raise ValueError(f"Unknown error code: {error_code}")

        return cls(
            coding=[
                producer_model.Coding(
                    system="https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                    code=error_code,
                    display=cls._TEXT_MAP[error_code],
                )
            ],
            text=cls._TEXT_MAP[error_code],
        )


class SpineErrorConcept(producer_model.CodeableConcept, consumer_model.CodeableConcept):
    _TEXT_MAP = {
        "NO_RECORD_FOUND": "No record found",
        "INVALID_NHS_NUMBER": "Invalid NHS number",
        "INVALID_CODE_SYSTEM": "Invalid code system",
        "INTERNAL_SERVER_ERROR": "Unexpected internal server error",
        "BAD_REQUEST": "Bad request",
        "AUTHOR_CREDENTIALS_ERROR": "Author credentials error",
    }

    @classmethod
    def from_code(cls, error_code: str) -> "SpineErrorConcept":
        if error_code not in cls._TEXT_MAP:
            raise ValueError(f"Unknown error code: {error_code}")

        return cls(
            coding=[
                producer_model.Coding(
                    system="https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                    code=error_code,
                    display=cls._TEXT_MAP[error_code],
                )
            ]
        )
