import json

from behave import then, when
from lambda_utils.tests.unit.utils import make_aws_event

from feature_tests.steps.aws.resources.api import producer_read_api_request
from feature_tests.steps.common.common_utils import render_template_document


@when(
    'Producer "{producer}" reads an existing Document Reference "{document_reference_id}"'
)
def producer_reads_existing_document_reference(
    context, producer, document_reference_id
):
    path_params = {"id": document_reference_id}
    headers = {
        "NHSD-Client-RP-Details": json.dumps(
            {
                "app.ASID": producer,
                "nrl.pointer-types": context.allowed_types,
            }
        )
    }

    if context.local_test:
        from api.producer.readDocumentReference.index import handler

        event = make_aws_event(pathParameters=path_params, headers=headers)
        response = handler(event)
        context.response_status_code = response["statusCode"]
        context.response_message = response["body"]
    else:
        response = producer_read_api_request(
            path_params=path_params.values(),
            headers=headers,
        )
        context.response_status_code = response.status_code
        context.response_message = response.text


@then("the response is the DOCUMENT template with the below values")
def the_response_is_the_template_with_values(context):
    assert json.loads(context.response_message) == json.loads(
        render_template_document(context=context)
    ), json.loads(context.response_message)
