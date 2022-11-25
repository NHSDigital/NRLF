import boto3
from behave import use_fixture

from feature_tests.steps.aws.resources.dynamodb import (
    FeatureTestDynamoRepository,
    get_dynamo_db_repository,
)
from feature_tests.steps.fixtures import (
    mock_document_pointer_dynamo_db,
    mock_environmental_variables,
)
from helpers.aws_session import new_aws_session


def _empty_dynamo_db_table(context, table_name: str):
    repository: FeatureTestDynamoRepository = get_dynamo_db_repository(
        context, table_name
    )
    repository.delete_all()


def before_all(context):
    if all(
        (
            context.config.userdata.get("sandbox_test"),
            context.config.userdata.get("integration_test"),
        )
    ):
        raise ValueError("Only one of integration_test and sandbox_test permitted")

    context.sandbox_test = (
        context.config.userdata.get("sandbox_test", "false") != "false"
    )

    context.local_test = (
        context.config.userdata.get("integration_test", "false") != "true"
    ) and not context.sandbox_test


def before_scenario(context, scenario):
    context.template = None
    context.template_document = None
    context.template_headers = None
    context.template_policy_response = None
    context.developer_headers = {}
    context.documents = {}
    context.query_parameters = {}
    context.headers = {}
    context.valid_producer = True
    context.response_status_code = None
    context.response_message = None
    context.producer_exists = True
    context.sent_document = None
    context.allowed_types = []

    if context.local_test:
        use_fixture(mock_environmental_variables, context)
        use_fixture(mock_document_pointer_dynamo_db, context)
        context.dynamodb_client = boto3.client("dynamodb")
    elif context.sandbox_test:
        context.dynamodb_client = boto3.client(
            "dynamodb", endpoint_url="http://localhost:4566"
        )
        _empty_dynamo_db_table(context, "Document Pointers")
    else:
        session = new_aws_session()
        context.dynamodb_client = session.client("dynamodb")
        _empty_dynamo_db_table(context, "Document Pointers")
