from typing import Union

from pydantic import ValidationError

from nrlf.core_pipeline.nhsd_codings import SpineCoding
from nrlf.producer.fhir.r4.model import RequestParams


class ItemNotFound(Exception):
    pass


class DynamoDbError(Exception):
    pass


class FhirValidationError(Exception):
    pass


class TooManyItemsError(Exception):
    pass


class ImmutableFieldViolationError(Exception):
    pass


class InvalidLogicalIdError(Exception):
    pass


class UnknownParameterError(Exception):
    pass


class DuplicateError(Exception):
    pass


class SupersedeError(Exception):
    pass


class DocumentReferenceValidationError(Exception):
    pass


class ProducerValidationError(Exception):
    pass


class InconsistentUpdateId(Exception):
    pass


class RequestValidationError(Exception):
    pass


class InconsistentUpdateId(Exception):
    pass


class SupersedeValidationError(Exception):
    pass


class InvalidTupleError(Exception):
    pass


class NextPageTokenValidationError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class ProducerCreateValidationError(Exception):
    pass


class MissingRequiredFieldForCreate(Exception):
    pass


class DuplicateKeyError(Exception):
    pass


class MalformedProducerId(ValueError):
    pass


class InconsistentProducerId(ValueError):
    pass


class BadJsonSchema(Exception):
    pass


class JsonSchemaValidationError(ValueError):
    pass


NRLF_TO_SPINE_4XX_ERROR = {
    AuthenticationError: SpineCoding.ACCESS_DENIED_LEVEL,
    DynamoDbError: SpineCoding.RESOURCE_NOT_FOUND,
    FhirValidationError: SpineCoding.VALIDATION_ERROR,
    ImmutableFieldViolationError: SpineCoding.VALIDATION_ERROR,
    ItemNotFound: SpineCoding.RESOURCE_NOT_FOUND,
    TooManyItemsError: SpineCoding.VALIDATION_ERROR,
    ValidationError: SpineCoding.VALIDATION_ERROR,
    UnknownParameterError: SpineCoding.VALIDATION_ERROR,
    DuplicateError: SpineCoding.INVALID_VALUE,
    SupersedeError: SpineCoding.INVALID_RESOURCE_ID,
    DocumentReferenceValidationError: SpineCoding.SERVICE_ERROR,
    RequestValidationError: SpineCoding.VALIDATION_ERROR,
    InconsistentUpdateId: SpineCoding.VALIDATION_ERROR,
    ProducerValidationError: SpineCoding.VALIDATION_ERROR,
    MissingRequiredFieldForCreate: SpineCoding.VALIDATION_ERROR,
    InconsistentUpdateId: SpineCoding.VALIDATION_ERROR,
    SupersedeValidationError: SpineCoding.VALIDATION_ERROR,
    InvalidTupleError: SpineCoding.VALIDATION_ERROR,
    NextPageTokenValidationError: SpineCoding.VALIDATION_ERROR,
    ProducerCreateValidationError: SpineCoding.VALIDATION_ERROR,
    DuplicateKeyError: SpineCoding.VALIDATION_ERROR,
    JsonSchemaValidationError: SpineCoding.VALIDATION_ERROR,
}


ERROR_SET_4XX = tuple(NRLF_TO_SPINE_4XX_ERROR.keys())


def assert_no_extra_params(
    request_params: RequestParams,
    provided_params: Union[list[str], None],
):
    if provided_params is None:
        return
    expected_params = request_params.dict(by_alias=True).keys()
    unknown_params = set(provided_params) - set(expected_params)
    if unknown_params:
        raise UnknownParameterError(
            f"Unexpected parameters: {', '.join(unknown_params)}"
        )
