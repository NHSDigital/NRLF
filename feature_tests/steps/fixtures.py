import os
from unittest import mock

import boto3
import moto
from behave import fixture
from nrlf.core.types import DynamoDbClient


@fixture(name="fixture.mock.document_pointer_dynamo_db")
def mock_document_pointer_dynamo_db(context, *args, **kwargs):
    with moto.mock_dynamodb() as client:
        client: DynamoDbClient = boto3.client("dynamodb")
        client.create_table(
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "nhs_number", "AttributeType": "S"},
            ],
            TableName="document-pointer",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "idx_nhs_number_by_id",
                    "KeySchema": [
                        {"AttributeName": "nhs_number", "KeyType": "HASH"},
                        {"AttributeName": "id", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 123,
                        "WriteCapacityUnits": 123,
                    },
                },
            ],
        )
        yield client


@fixture(name="fixture.mock.environmental_variables")
def mock_environmental_variables(context, *args, **kwargs):
    with mock.patch.dict(
        os.environ,
        {
            "AWS_REGION": "eu-west-2",
            "PREFIX": "",
            "DOCUMENT_POINTER_TABLE_NAME": "document-pointer",
            "AWS_DEFAULT_REGION": "eu-west-2",
        },
        clear=True,
    ):
        yield
