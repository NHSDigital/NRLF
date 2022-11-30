import json

from behave import given, then
from nrlf.core.dynamodb_types import convert_dynamo_value_to_raw_value
from nrlf.core.errors import ItemNotFound
from nrlf.core.transform import create_document_pointer_from_fhir_json
from nrlf.core.validators import validate_timestamp

from feature_tests.steps.aws.resources.dynamodb import get_dynamo_db_repository
from feature_tests.steps.common.common_utils import (
    render_fhir_template,
    render_template,
    uuid_headers,
)
from layer.nrlf.nrlf.core.model import Auth


@given("template DOCUMENT")
def set_template_document(context):
    context.template = context.text


@given("example HEADERS")
def set_template_headers(context):
    context.template_headers = context.text


@given("template POLICY_RESPONSE")
def set_template(context):
    context.template = context.text


@given("a request for {organisation} contains all the correct headers to be authorised")
def request_contains_correct_headers(context, organisation):
    auth_headers = {
        "request-type": "app_restricted",
        "Accept": "version=1",
        "Authorization": "letmein",
    }
    context.headers = auth_headers
    context.headers["Organisation-Code"] = json.loads(organisation)
    context.headers.update(**uuid_headers(context))


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


@then("the request is explicitly denied")
def assert_request_denied(context):
    assert context.response_status_code == 403, (
        context.response_message,
        context.response_status_code,
    )


@then('the response contains error message "{error_message}"')
def assert_error_message(context, error_message: str):
    actual_error_message = json.loads(context.response_message)["issue"][0][
        "diagnostics"
    ]
    assert actual_error_message == error_message, actual_error_message


@given("an Auth detail exists in the system with the below values")
def given_auth_details_exists(context):
    auth_repository = get_dynamo_db_repository(context, "Auth")
    rendered_template = render_template(context, context.template_auth)
    auth_json = json.loads(rendered_template)
    context.allowed_types = auth_json["document_types"]
    auth_repository.create(Auth(**auth_json))


@given("the following organisation to application relationship exists")
def given_application_and_organisation_relationship(context):
    for row in context.table:
        context.template_auth["id"] = row["organisation"]
        context.template_auth["application_id"] = row["application"]


@given("{organisation} can access the following document types")
def given_organisation_document_types(context, organisation):
    document_types = []
    for row in context.table:
        system = row["system"]
        value = row["value"]
        document_type = f"{system}|{value}"
        document_types.append(document_type)

    context.template_auth["document_types"] = document_types

    auth_repository = get_dynamo_db_repository(context, "Auth")
    context.allowed_types = document_types
    auth_repository.create(Auth(**context.template_auth))


@given("a Document Pointer exists in the system with the below values")
def given_document_pointer_exists(context):
    document_pointer_repository = get_dynamo_db_repository(context, "Document Pointers")
    rendered_template = render_fhir_template(context, context.template)
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
    except ItemNotFound:
        return
    except Exception as e:
        item = e
    assert False, item


@then("returns the correct allow policy")
def response_contains_correct_allow_policy(context):
    headers = {**context.developer_headers, **context.headers}
    headers = _remove_authorisation_headers(headers)

    expected = json.loads(render_template(context, context.template))
    expected["context"] = {**headers}
    expected["principalId"] = headers["nhsd-correlation-id"]
    expected = json.dumps(expected)

    assert json.loads(expected) == json.loads(json.dumps(context.response_message))


@then("returns the correct deny policy")
def response_contains_correct_deny_policy(context):
    headers = {**context.developer_headers, **context.headers}
    headers = _remove_authorisation_headers(headers)

    expected = json.loads(render_template(context, context.template))
    expected["context"] = {**headers}
    expected["principalId"] = headers["nhsd-correlation-id"]
    expected = json.dumps(expected)

    assert json.loads(expected) == json.loads(json.dumps(context.response_message))


def _remove_authorisation_headers(headers):
    headers.pop("Authorization")
    headers.pop("Accept")
    headers.pop("x-request-id")
    headers.pop("Organisation-Code")
    return headers


def _remove_consumer_authorisation_headers(headers):
    headers.pop("Authorization")
    headers.pop("Accept")
    headers.pop("x-request-id")
    return headers
