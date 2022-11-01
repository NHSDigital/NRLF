import boto3
from behave import use_fixture

from feature_tests.steps.aws.resources.common import new_aws_session
from feature_tests.steps.fixtures import (
    mock_document_pointer_dynamo_db,
    mock_environmental_variables,
)


def before_all(context):
    context.local_test = False


def before_scenario(context, scenario):
    context.template_document = None
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
    else:
        session = new_aws_session()
        context.dynamodb_client = session.client("dynamodb")


def before_tag(context, tag):
    context.local_test = tag == "local"
