import boto3
from behave import use_fixture

from feature_tests.steps.fixtures import (
    mock_document_pointer_dynamo_db,
    mock_environmental_variables,
)


def before_scenario(context, scenario):
    context.template_document = ""
    context.valid_producer = True
    context.response_status_code = None
    context.response_message = None
    context.producer_exists = True
    context.dynamodb_client = boto3.client("dynamodb")
    context.sent_document = None


def before_tag(context, tag):
    if tag == "local":
        use_fixture(mock_environmental_variables, context)
        use_fixture(mock_document_pointer_dynamo_db, context)
