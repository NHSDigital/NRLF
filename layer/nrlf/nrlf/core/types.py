from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_s3 import S3Client

__all__ = ["S3Client", "DynamoDBClient", "LambdaClient"]


class S3Exceptions:
    class NoSuchKey(Exception):
        pass
