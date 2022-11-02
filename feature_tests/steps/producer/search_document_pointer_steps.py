import json
from unittest import mock

from behave import then, when
from lambda_pipeline.types import LambdaContext
from lambda_utils.tests.unit.utils import make_aws_event

from feature_tests.steps.aws.resources.api import document_pointer_api_request
from feature_tests.steps.common.common_utils import render_template_document


@then("the response contains the DOCUMENT template with the below values")
def the_response_contains_the_template_with_values(context):
    response = json.loads(context.response_message)

    document_references = [entry["resource"] for entry in response["entry"]]

    assert json.loads(render_template_document(context=context)) in document_references


@then("{number_of_documents:d} document references were returned")
def the_response_is_the_list_of_template_documents(context, number_of_documents: int):

    response = json.loads(context.response_message)
    assert number_of_documents == response["total"]


@when('"{producer}" searches with query parameters')
def producer_search_document_pointers(context, producer: str):
    query_parameters = {
        row["property"]: row["value"] for row in context.table if row["value"] != "null"
    }

    context.query_parameters = query_parameters


@when('"{producer}" searches with the header values')
def producer_search_document_pointers(context, producer: str):
    headers = {row["property"]: row["value"] for row in context.table}

    context.headers = headers


@then("the response is an empty bundle")
def producer_search_document_pointers(context):
    response = context.response_message

    empty_bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 0,
        "entry": [],
    }

    assert json.loads(response) == empty_bundle


@then("the search is made")
def producer_search_document_pointers(context):
    from api.producer.searchDocumentReference.index import handler

    queryStringParameters = context.query_parameters
    headers = {
        "NHSD-Client-RP-Details": json.dumps(
            {
                "app.ASID": context.headers["custodian"],
                "nrl.pointer-types": context.allowed_types,
            }
        )
    }

    if context.local_test:
        event = make_aws_event(
            queryStringParameters=queryStringParameters, headers=headers
        )
        lambda_context = LambdaContext()
        response = handler(event, lambda_context)
        context.response_status_code = response["statusCode"]
        context.response_message = response["body"]
    else:
        response = document_pointer_api_request(method="POST", headers=headers)
        context.response_status_code = response.status_code
        context.response_message = response.text
