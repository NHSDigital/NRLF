import json

from behave import when
from lambda_pipeline.types import LambdaContext

from feature_tests.steps.aws.resources.api import consumer_authoriser_lambda
from feature_tests.steps.common.common_utils import (
    make_aws_authoriser_event,
    uuid_headers,
)


@when('Consumer "{requestor}" makes a request')
def request_contains_correct_headers(context, requestor):

    developer_headers = {
        row["property"]: row["value"] for row in context.table if row["value"] != "null"
    }
    context.developer_headers = developer_headers

    headers = {
        "NHSD-Client-RP-Details": json.dumps(
            {"app.ASID": "foobar", "nrl.pointer-types": ["type1"], **developer_headers}
        ),
        **uuid_headers(context),
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
        response = consumer_authoriser_lambda(event=event, sandbox=context.sandbox_test)
        context.response_message = response
