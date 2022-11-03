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
