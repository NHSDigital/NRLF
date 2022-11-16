import json

from behave import when
from lambda_utils.tests.unit.utils import make_aws_event

from feature_tests.steps.aws.resources.api import consumer_read_api_request
from feature_tests.steps.common.common_utils import uuid_headers


@when(
    'Consumer "{consumer}" reads an existing Document Reference "{document_reference_id}"'
)
def consumer_reads_existing_document_reference(
    context, consumer, document_reference_id
):
    path_params = {"id": document_reference_id}
    headers = {
        "NHSD-Client-RP-Details": json.dumps(
            {
                "app.ASID": "foobar",
                "nrl.pointer-types": context.allowed_types,
            }
        ),
        **uuid_headers(context),
    }

    if context.local_test:
        from api.consumer.readDocumentReference.index import handler

        event = make_aws_event(pathParameters=path_params, headers=headers)
        response = handler(event)
        context.response_status_code = response["statusCode"]
        context.response_message = response["body"]
    else:
        response = consumer_read_api_request(
            path_params=path_params.values(),
            headers=headers,
            sandbox=context.sandbox_test,
        )
        context.response_status_code = response.status_code
        context.response_message = response.text
