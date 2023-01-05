from nrlf.core.nhsd_codings import SpineCoding
from nrlf.producer.fhir.r4.model import RequestParams
from pydantic import ValidationError


class ItemNotFound(Exception):
    pass


class DynamoDbError(Exception):
    pass


class AuthenticationError(Exception):
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


NRLF_TO_SPINE_4XX_ERROR = {
    AuthenticationError: SpineCoding.ACCESS_DENIED_LEVEL,
    DynamoDbError: SpineCoding.RESOURCE_NOT_FOUND,
    FhirValidationError: SpineCoding.VALIDATION_ERROR,
    ImmutableFieldViolationError: SpineCoding.VALIDATION_ERROR,
    ItemNotFound: SpineCoding.RESOURCE_NOT_FOUND,
    TooManyItemsError: SpineCoding.NOT_ACCEPTABLE,
    ValidationError: SpineCoding.VALIDATION_ERROR,
    UnknownParameterError: SpineCoding.VALIDATION_ERROR,
    DuplicateError: SpineCoding.INVALID_RESOURCE_ID,
    SupersedeError: SpineCoding.INVALID_RESOURCE_ID,
}


ERROR_SET_4XX = tuple(NRLF_TO_SPINE_4XX_ERROR.keys())


def assert_no_extra_params(
    request_params: RequestParams,
    provided_params: list[str],
):
    expected_params = request_params.dict(by_alias=True).keys()
    unknown_params = set(provided_params) - set(expected_params)
    if unknown_params:
        raise UnknownParameterError(
            f"Unexpected query parameters: {', '.join(unknown_params)}"
        )
