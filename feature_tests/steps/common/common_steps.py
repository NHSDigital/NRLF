import json

from behave import given, then
from nrlf.core.dynamodb_types import convert_dynamo_value_to_raw_value
from nrlf.core.errors import ItemNotFound
from nrlf.core.transform import create_document_pointer_from_fhir_json
from nrlf.core.validators import validate_timestamp

from feature_tests.steps.aws.resources.dynamodb import get_dynamo_db_repository
from feature_tests.steps.common.common_utils import (
    render_template
)


@given("template DOCUMENT")
def set_template_document(context):
    context.template = context.text


@given("example HEADERS")
def set_template_headers(context):
    context.template_headers = context.text


@given("template POLICY_RESPONSE")
def set_template_headers(context):
    context.template = context.text


@given("a request contains all the correct headers to be authorised")
def request_contains_correct_headers(context):
    context.headers = json.loads(context.template_headers)


@given('{actor_type} "{actor_name}" has permission to {action} Document Pointers for')
def given_permissions_for_types(context, actor_type: str, actor_name: str, action: str):
    context.allowed_types += [
        f'https://snomed.info/ict|{row["snomed_code"]}' for row in context.table
    ]


@then("the operation is unsuccessful")
def assert_operation_unsuccessful(context):
    assert context.response_status_code == 400, (
        context.response_message,
        context.response_status_code,
    )


@then('the response contains error message "{error_message}"')
def assert_error_message(context, error_message: str):
    actual_error_message = json.loads(context.response_message)["issue"][0][
        "diagnostics"
    ]
    assert actual_error_message == error_message, actual_error_message


@given("a Document Pointer exists in the system with the below values")
def given_document_pointer_exists(context):
    document_pointer_repository = get_dynamo_db_repository(context, "Document Pointers")
    rendered_template = render_template(context)
    body = json.loads(rendered_template)
    core_model = create_document_pointer_from_fhir_json(body, api_version=1)
    document_pointer_repository.create(core_model)

    context.documents[body["id"]] = rendered_template


@then("the operation is successful")
def assert_operation_successful(context):
    assert context.response_status_code == 200, (
        context.response_message,
        context.response_status_code,
    )


@then('Document Pointer "{document_id}" exists')
def assert_document_pointer_exists(context, document_id: str):
    document_pointer_client = get_dynamo_db_repository(context, "Document Pointers")
    item = document_pointer_client.read(
        KeyConditionExpression="id = :id",
        ExpressionAttributeValues={":id": {"S": document_id}},
    )
    for row in context.table:
        dynamo_value = convert_dynamo_value_to_raw_value(getattr(item, row["property"]))
        property_type = type(dynamo_value)
        if row["value"] == "<<template>>":
            assert dynamo_value == context.sent_document, dynamo_value
        elif row["value"] == "NULL":
            assert dynamo_value is None
        elif row["value"] == "<<timestamp>>":
            validate_timestamp(dynamo_value)
        else:
            assert dynamo_value == property_type(
                row["value"]
            ), f'expected {row["value"]} got {dynamo_value}'


@then('Document Pointer "{document_id}" does not exist')
def assert_document_pointer_exists(context, document_id: str):
    document_pointer_client = get_dynamo_db_repository(context, "Document Pointers")
    item = None
    try:
        item = document_pointer_client.read(
            KeyConditionExpression="id = :id",
            ExpressionAttributeValues={":id": {"S": document_id}},
        )
<<<<<<< HEAD
    except ItemNotFound:
        return
    except Exception as e:
        item = e
    assert False, item
=======


@then("returns the correct policy")
def response_contains_correct_policy(context):
    headers = {**context.developer_headers, **context.headers}
    headers = _remove_authorisation_headers(headers)

    expected = json.loads(render_template(context))
    expected["context"] = headers

    expected = json.dumps(expected)

    assert json.loads(expected) == json.loads(json.dumps(context.response_message))


def _remove_authorisation_headers(headers):
    headers.pop("Authorization")
    headers.pop("Accept")
    headers.pop("x-request-id")
    return headers
>>>>>>> 7d09056 (feautre/nrlf-158-lambda-authoriser le squash)
