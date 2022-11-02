import boto3
from behave import use_fixture

from feature_tests.steps.aws.resources.common import new_aws_session
from feature_tests.steps.aws.resources.dynamodb import (
    FeatureTestDynamoRepository,
    get_dynamo_db_repository,
)
from feature_tests.steps.fixtures import (
    mock_document_pointer_dynamo_db,
    mock_environmental_variables,
)


def _empty_dynamo_db_table(context, table_name: str):
    repository: FeatureTestDynamoRepository = get_dynamo_db_repository(
        context, table_name
    )
    repository.delete_all()


def before_all(context):
    context.local_test = (
        context.config.userdata.get("integration_test", "false") != "true"
    )


def before_scenario(context, scenario):
    context.template_document = None
    context.response_status_code = None
    context.response_message = None
    context.producer_exists = True
    context.sent_document = None
    context.producer_allowed_types = []

    if context.local_test:
        use_fixture(mock_environmental_variables, context)
        use_fixture(mock_document_pointer_dynamo_db, context)
        context.dynamodb_client = boto3.client("dynamodb")
    else:
        session = new_aws_session()
        context.dynamodb_client = session.client("dynamodb")
        _empty_dynamo_db_table(context, "Document Pointers")
