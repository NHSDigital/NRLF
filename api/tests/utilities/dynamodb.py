import boto3

from nrlf.core.config import Config
from nrlf.core.dynamodb.repository import DocumentPointerRepository
from nrlf.core.types import DynamoDBServiceResource


def create_document_pointer_table(config: Config, dynamodb: DynamoDBServiceResource):
    return dynamodb.create_table(
        TableName=config.PREFIX + "document-pointer",
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
            {"AttributeName": "pk_1", "AttributeType": "S"},
            {"AttributeName": "sk_1", "AttributeType": "S"},
            {"AttributeName": "pk_2", "AttributeType": "S"},
            {"AttributeName": "sk_2", "AttributeType": "S"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        GlobalSecondaryIndexes=[
            {
                "IndexName": "idx_gsi_1",
                "KeySchema": [
                    {"AttributeName": "pk_1", "KeyType": "HASH"},
                    {"AttributeName": "sk_1", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "idx_gsi_2",
                "KeySchema": [
                    {"AttributeName": "pk_2", "KeyType": "HASH"},
                    {"AttributeName": "sk_2", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    )


def mock_repository(func):
    def wrapped_function(*args, **kwargs):
        config = Config()
        dynamodb = boto3.resource("dynamodb")
        create_document_pointer_table(config, dynamodb)

        repository = DocumentPointerRepository(
            dynamodb=dynamodb, environment_prefix=config.PREFIX
        )

        return func(*args, **kwargs, repository=repository)

    return wrapped_function
