import json

from behave import then, when
from lambda_pipeline.types import LambdaContext

from feature_tests.steps.aws.resources.api import consumer_authoriser_lambda
from feature_tests.steps.common.common_steps import (
    _remove_consumer_authorisation_headers,
)
from feature_tests.steps.common.common_utils import (
    make_aws_authoriser_event,
    render_template,
)


@then("returns the correct allow policy to consumer")
def response_contains_correct_allow_policy_consumer(context):
    headers = {**context.developer_headers, **context.headers}
    headers = _remove_consumer_authorisation_headers(headers)
    document_types = {"document_types": json.dumps(context.allowed_types)}

    expected = json.loads(render_template(context, context.template))
    expected["context"] = {**document_types, **headers}
    expected["principalId"] = headers["nhsd-correlation-id"]

    expected = json.dumps(expected)

    assert json.loads(expected) == json.loads(json.dumps(context.response_message))


@then("returns the correct deny policy to consumer")
def response_contains_correct_deny_policy(context):
    headers = {**context.developer_headers, **context.headers}
    headers = _remove_consumer_authorisation_headers(headers)

    expected = json.loads(render_template(context, context.template))
    expected["context"] = {**headers}
    expected["principalId"] = headers["nhsd-correlation-id"]
    expected = json.dumps(expected)

    assert json.loads(expected) == json.loads(json.dumps(context.response_message))


@when("consumer {organisation} makes a request")
def consumer_request_contains_correct_headers(context, organisation):

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
        from api.consumer.authoriser.index import handler

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
        response = consumer_authoriser_lambda(event=event)
        context.response_message = response
