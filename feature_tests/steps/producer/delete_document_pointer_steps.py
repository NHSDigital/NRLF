import json

from behave import then, when
from lambda_utils.tests.unit.utils import make_aws_event

from feature_tests.steps.aws.resources.api import (
    producer_delete_api_request,
    producer_read_api_request,
)
from feature_tests.steps.common.common_utils import (
    authorisation_headers,
    render_fhir_template,
    uuid_headers,
)


@when(
    'Producer "{producer}" deletes an existing Document Reference "{document_reference_id}" as {organisation}'
)
def producer_deletes_existing_document_reference(
    context, producer, document_reference_id, organisation
):

    path_params = {"id": document_reference_id}
    headers = {
        "NHSD-Client-RP-Details": json.dumps(
            {
                "app.ASID": producer,
                "nrl.pointer-types": context.allowed_types,
                "developer.app.id": "application id",
                "developer.app.name": "application name",
            }
        ),
        **uuid_headers(context),
        **authorisation_headers(context, organisation),
    }

    if context.local_test:
        from api.producer.deleteDocumentReference.index import handler

        event = make_aws_event(pathParameters=path_params, headers=headers)
        response = handler(event)
        context.response_status_code = response["statusCode"]
        context.response_message = response["body"]
    else:
        response = producer_delete_api_request(
            path_params=path_params.values(),
            headers=headers,
            sandbox=context.sandbox_test,
        )
        context.response_status_code = response.status_code
        context.response_message = response.text


@then('the response contains success message "Resource removed"')
def the_response_is_the_template_with_values(context):
    assert context.response_message == '{"message": "Resource removed"}'
