import json
from unittest.mock import patch

from behave import then
from lambda_pipeline.types import LambdaContext
from lambda_utils.tests.unit.utils import make_aws_event

from feature_tests.steps.aws.resources.api import consumer_search_api_request


@then("the consumer search is made")
def producer_search_document_pointers(context):

    queryStringParameters = context.query_parameters
    headers = {
        "NHSD-Client-RP-Details": json.dumps(
            {
                "app.ASID": "foobar",
                "nrl.pointer-types": context.allowed_types,
            }
        )
    }

    if context.local_test:
        from api.consumer.searchDocumentReference.index import handler

        event = make_aws_event(
            queryStringParameters=queryStringParameters, headers=headers
        )
        lambda_context = LambdaContext()
        response = handler(event, lambda_context)
        context.response_status_code = response["statusCode"]
        context.response_message = response["body"]
    else:
        response = consumer_search_api_request(
            headers=headers, params=queryStringParameters
        )
        context.response_status_code = response.status_code
        context.response_message = response.text
