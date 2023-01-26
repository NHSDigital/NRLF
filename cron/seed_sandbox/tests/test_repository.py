import boto3
import moto
from nrlf.core.repository import Repository
from nrlf.core.types import DynamoDbClient

from cron.seed_sandbox.tests.utils import create_table


@moto.mock_dynamodb()
def test_repository_object_initialisation_with_existing_data():
    item_type_name = "document-pointer"
    client: DynamoDbClient = boto3.client("dynamodb")
    create_table(client=client, item_type_name=item_type_name)
    repository = Repository()
    pass
