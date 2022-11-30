import json

from behave import when
from lambda_utils.tests.unit.utils import make_aws_event

from feature_tests.steps.aws.resources.api import consumer_read_api_request
from feature_tests.steps.common.common_utils import authorisation_headers, uuid_headers


@when(
    'Consumer "{consumer}" reads an existing Document Reference "{document_reference_id}" as {organisation}'
)
def consumer_reads_existing_document_reference(
    context, consumer, document_reference_id, organisation
):
    path_params = {"id": document_reference_id}
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
        from api.consumer.readDocumentReference.index import handler

        authorizer = {"document_types": json.dumps(context.allowed_types)}

        event = make_aws_event(
            pathParameters=path_params, headers=headers, authorizer=authorizer
        )
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
