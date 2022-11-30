import json

from behave import when
from lambda_pipeline.types import LambdaContext

from feature_tests.steps.aws.resources.api import producer_authoriser_lambda
from feature_tests.steps.common.common_utils import (
    authorisation_headers,
    make_aws_authoriser_event,
    uuid_headers,
)


@when("producer {organisation} makes a request")
def producer_request_contains_correct_headers(context, organisation):

    developer_headers = {
        row["property"]: row["value"] for row in context.table if row["value"] != "null"
    }
    context.developer_headers = developer_headers

    headers = {
        "NHSD-Client-RP-Details": json.dumps(
            {"app.ASID": "foobar", "nrl.pointer-types": ["type1"], **developer_headers}
        ),
        **context.headers,
    }

    if context.local_test:
        from api.producer.authoriser.index import handler

        event = make_aws_authoriser_event(
            headers=headers, methodArn={"methodArn": "methodarn"}
        )

        lambda_context = LambdaContext()
        response = handler(event, lambda_context)
        context.response_message = response
    else:
        event = make_aws_authoriser_event(
            headers=headers, methodArn={"methodArn": "methodarn"}
        )
        response = producer_authoriser_lambda(event=event)
        context.response_message = response
