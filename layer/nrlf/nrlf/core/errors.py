class ItemNotFound(Exception):
    def __init__(self):
        super().__init__(f"Item could not be found")


class DynamoDbError(Exception):
    pass


class AuthenticationError(Exception):
    pass
