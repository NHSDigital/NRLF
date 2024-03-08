from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_s3 import S3Client

__all__ = ["DynamoDBServiceResource", "S3Client", "LambdaClient", "DynamoDBClient"]


class S3Exceptions:
    class NoSuchKey(Exception):
        pass
