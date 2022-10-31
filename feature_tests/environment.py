import boto3
from behave import use_fixture

from feature_tests.steps.fixtures import (
    mock_document_pointer_dynamo_db,
    mock_environmental_variables,
)


def before_all(context):
    context.local_tests = False


def before_scenario(context, scenario):
    context.template_document = None
    context.valid_producer = True
    context.response_status_code = None
    context.response_message = None
    context.producer_exists = True
    context.sent_document = None
    context.producer_allowed_types = []

    if context.local_tests:
        use_fixture(mock_environmental_variables, context)
        use_fixture(mock_document_pointer_dynamo_db, context)

    context.dynamodb_client = boto3.client("dynamodb")


def before_tag(context, tag):
    context.local_tests = tag == "local"
