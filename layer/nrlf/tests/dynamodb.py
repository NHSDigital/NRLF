from nrlf.core.boto import get_dynamodb_resource
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
            {"AttributeName": "patient_key", "AttributeType": "S"},
            {"AttributeName": "patient_sort", "AttributeType": "S"},
            {"AttributeName": "masterid_key", "AttributeType": "S"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        GlobalSecondaryIndexes=[
            {
                "IndexName": "patient_gsi",
                "KeySchema": [
                    {"AttributeName": "patient_key", "KeyType": "HASH"},
                    {"AttributeName": "patient_sort", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "masterid_gsi",
                "KeySchema": [
                    {"AttributeName": "masterid_key", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    )


def mock_repository(func):
    def wrapped_function(*args, **kwargs):
        config = Config()
        dynamodb = get_dynamodb_resource()
        create_document_pointer_table(config, dynamodb)

        repository = DocumentPointerRepository(environment_prefix=config.PREFIX)

        return func(*args, **kwargs, repository=repository)

    return wrapped_function
