import json

from behave import when
from lambda_pipeline.types import LambdaContext
from lambda_utils.tests.unit.utils import make_aws_event

from feature_tests.steps.aws.resources.api import producer_update_api_request
from feature_tests.steps.common.common_utils import (
    authorisation_headers,
    render_fhir_template,
    uuid_headers,
)


@when(
    'Producer "{producer}" updates a Document Reference "{document_reference_id}" from DOCUMENT template as {organisation}'
)
def producer_update_document_pointer_from_template(
    context, producer: str, document_reference_id, organisation
):
    body = render_fhir_template(context, context.template)
    path_params = {"id": document_reference_id}
    headers = {
        "NHSD-Client-RP-Details": json.dumps(
            {
                "app.ASID": producer if context.producer_exists else "",
                "nrl.pointer-types": context.allowed_types,
                "developer.app.id": "application id",
                "developer.app.name": "application name",
            }
        ),
        **uuid_headers(context),
        **authorisation_headers(context, organisation),
    }
    context.sent_document = json.dumps(json.loads(body))
    if context.local_test:
        from api.producer.updateDocumentReference.index import handler

        event = make_aws_event(
            body=body,
            headers=headers,
            pathParameters=path_params,
        )
        lambda_context = LambdaContext()
        response = handler(event, lambda_context)
        context.response_status_code = response["statusCode"]
        context.response_message = response["body"]
    else:
        response = producer_update_api_request(
            data=body,
            headers=headers,
            path_params=path_params.values(),
            sandbox=context.sandbox_test,
        )
        context.response_status_code = response.status_code
        context.response_message = response.text
