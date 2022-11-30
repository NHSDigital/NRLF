import json

from behave import then, when
from lambda_pipeline.types import LambdaContext
from lambda_utils.tests.unit.utils import make_aws_event

from feature_tests.steps.aws.resources.api import (
    consumer_search_api_request,
    consumer_search_api_request_post,
)
from feature_tests.steps.common.common_utils import authorisation_headers, uuid_headers


@then("the consumer search is made as {organisation}")
def consumer_search_document_pointers(context, organisation):

    queryStringParameters = context.query_parameters
    developer_headers = {
        row["property"]: row["value"] for row in context.table if row["value"] != "null"
    }
    context.developer_headers = developer_headers
    headers = {
        "NHSD-Client-RP-Details": json.dumps(
            {
                "app.ASID": "foobar",
                "nrl.pointer-types": context.allowed_types,
                **developer_headers,
            }
        ),
        **uuid_headers(context),
        **authorisation_headers(context, organisation),
    }

    if context.local_test:
        from api.consumer.searchDocumentReference.index import handler

        authorizer = {"document_types": json.dumps(context.allowed_types)}

        event = make_aws_event(
            queryStringParameters=queryStringParameters,
            headers=headers,
            authorizer=authorizer,
        )
        lambda_context = LambdaContext()
        response = handler(event, lambda_context)
        context.response_status_code = response["statusCode"]
        context.response_message = response["body"]
    else:
        response = consumer_search_api_request(
            headers=headers, params=queryStringParameters, sandbox=context.sandbox_test
        )
        context.response_status_code = response.status_code
        context.response_message = response.text


@when('"{consumer}" searches with body parameters')
def consumer_search_document_pointers(context, consumer: str):
    body = {
        row["property"]: row["value"] for row in context.table if row["value"] != "null"
    }
    context.body = body


@then("the consumer search is made by POST as {organisation}")
def consumer_search_document_pointers_by_post(context, organisation):
    body = context.body
    developer_headers = {
        row["property"]: row["value"] for row in context.table if row["value"] != "null"
    }
    context.developer_headers = developer_headers
    headers = {
        "NHSD-Client-RP-Details": json.dumps(
            {
                "app.ASID": "foobar",
                "nrl.pointer-types": context.allowed_types,
                **developer_headers,
            }
        ),
        **uuid_headers(context),
        **authorisation_headers(context, organisation),
    }

    if context.local_test:
        from api.consumer.searchPostDocumentReference.index import handler

        authorizer = {"document_types": json.dumps(context.allowed_types)}

        event = make_aws_event(
            body=json.dumps(body), headers=headers, authorizer=authorizer
        )
        lambda_context = LambdaContext()
        response = handler(event, lambda_context)
        context.response_status_code = response["statusCode"]
        context.response_message = response["body"]
    else:
        response = consumer_search_api_request_post(
            headers=headers,
            data=json.dumps(context.body),
            path_params=["_search"],
            sandbox=context.sandbox_test,
        )
        context.response_status_code = response.status_code
        context.response_message = response.text
