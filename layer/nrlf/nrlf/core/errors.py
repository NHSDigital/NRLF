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


ERROR_SET_4XX = (
    AuthenticationError,
    DynamoDbError,
    FhirValidationError,
    ImmutableFieldViolationError,
    ItemNotFound,
    TooManyItemsError,
    ValidationError,
)
