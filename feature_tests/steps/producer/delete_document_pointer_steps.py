import json

from behave import then, when
from lambda_utils.tests.unit.utils import make_aws_event

from feature_tests.steps.common.common_utils import render_template_document


@when(
    'Producer "{producer}" deletes an existing Document Reference "{document_reference_id}"'
)
def producer_deletes_existing_document_reference(
    context, producer, document_reference_id
):
    from api.producer.deleteDocumentReference.index import handler

    event = make_aws_event(
        pathParameters={"id": f"{producer}|{document_reference_id}"},
        headers={
            "NHSD-Client-RP-Details": json.dumps(
                {
                    "app.ASID": producer,
                    "nrl.pointer-types": context.producer_allowed_types,
                }
            )
        },
    )

    response = handler(event)
    context.response_status_code = response["statusCode"]
    context.response_message = response["body"]


@then('the response contains success message "Resource removed"')
def the_response_is_the_template_with_values(context):
    assert context.response_message == '{"message": "Resource removed"}'
