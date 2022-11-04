class DynamoDbResponse(dict):
    """For type-annotating boto3.client('dynamodb') responses"""

    pass


class DynamoDbClient:
    """For type-annotating boto3.client('dynamodb')"""

    def get_item(self, *args, **kwargs) -> DynamoDbResponse:
        pass

    def put_item(self, *args, **kwargs) -> DynamoDbResponse:
        pass

    def update_item(self, *args, **kwargs) -> DynamoDbResponse:
        pass

    def delete_item(self, *args, **kwargs) -> DynamoDbResponse:
        pass

    def query(self, *args, **kwargs) -> DynamoDbResponse:
        pass

    def transact_write_items(self, *args, **kwargs) -> DynamoDbResponse:
        pass

    def scan(self, *args, **kwargs) -> DynamoDbResponse:
        pass

    def create_table(self, *args, **kwargs) -> DynamoDbResponse:
        pass

    def delete_table(self, *args, **kwargs) -> DynamoDbResponse:
        pass
