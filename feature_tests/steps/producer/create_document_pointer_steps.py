import json
from unittest import mock

from behave import given, when
from lambda_pipeline.types import LambdaContext
from lambda_utils.tests.unit.utils import make_aws_event

from feature_tests.steps.common.common_utils import render_template_document


@given('Producer "{producer}" has permission to create Document Pointers for')
def given_producer_has_permission(context, producer: str):
    context.valid_producer = True


@given('Producer "{producer}" does not exist in the system')
def given_producer_not_exist(context, producer: str):
    context.producer_exists = False


@given('Producer "{producer}" does not have permission to create Document Pointers for')
def given_producer_no_permission(context, producer: str):
    context.valid_producer = False


@when('Producer "{producer}" creates a Document Reference from DOCUMENT template')
def producer_create_document_pointer_from_template(context, producer: str):
    from api.producer.createDocumentReference.index import handler

    body = render_template_document(context)
    context.sent_document = json.dumps(json.loads(body))
    event = make_aws_event(body=body)
    lambda_context = LambdaContext()

    with mock.patch(
        "api.producer.createDocumentReference.src.v1.handler._is_valid_producer",
        return_value=context.valid_producer,
    ), mock.patch(
        "api.producer.createDocumentReference.src.v1.handler._producer_exists",
        return_value=context.producer_exists,
    ):
        response = handler(event, lambda_context)
        context.response_status_code = response["statusCode"]
        context.response_message = response["body"]
