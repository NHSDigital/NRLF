class DynamoDbResponse(dict):
    """For type-annotating boto3.client('dynamodb') responses"""


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


class S3Exceptions:
    class NoSuchKey(Exception):
        pass


class S3Client:
    """For type-annotating boto3.client('s3')"""

    @property
    def exceptions(self):
        return S3Exceptions

        class NoSuchKey(Exception):
            pass

    def create_bucket(self, Bucket: str, **kwargs) -> dict:
        pass

    def get_object(self, Bucket: str, Key: str) -> dict:
        pass

    def put_object(self, Bucket: str, Key: str, Body: bytes) -> dict:
        pass
