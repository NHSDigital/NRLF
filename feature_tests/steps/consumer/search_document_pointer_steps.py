import json
from unittest.mock import patch

from behave import then
from lambda_pipeline.types import LambdaContext
from lambda_utils.tests.unit.utils import make_aws_event


@then("the consumer searches for document references")
def consumer_search_document_pointers(context):
    from api.consumer.searchDocumentReference.index import handler

    queryStringParameters = context.query_parameters

    event = make_aws_event(
        queryStringParameters=queryStringParameters,
        headers={
            "NHSD-Client-RP-Details": json.dumps(
                {
                    "nrl.pointer-types": context.allowed_types,
                }
            )
        },
    )

    lambda_context = LambdaContext()

    with patch(
        "api.consumer.searchDocumentReference.src.v1.handler._is_valid_consumer",
        return_value=context.valid_consumer,
    ), patch(
        "api.producer.searchDocumentReference.src.v1.handler._consumer_exists",
        return_value=context.consumer_exists,
    ):
        response = handler(event, lambda_context)
        context.response_status_code = response["statusCode"]
        context.response_message = response["body"]
