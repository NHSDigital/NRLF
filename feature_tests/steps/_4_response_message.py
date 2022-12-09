import json
from dataclasses import asdict

from behave.runner import Context
from nrlf.producer.fhir.r4.strict_model import Bundle

from feature_tests.common.decorators import then
from feature_tests.common.models import TestConfig


@then("the response is the {template_name} template with the below values")
def the_response_is_the_template_with_values(context: Context, template_name: str):
    test_config: TestConfig = context.test_config
    rendered = test_config.templates[template_name].render_fhir(table=context.table)
    fhir_json = json.loads(rendered)
    assert test_config.response.dict == fhir_json, test_config.response.dict


@then("the response is a Bundle with {count:d} entries")
def producer_search_document_pointers(context: Context, count: int):
    test_config: TestConfig = context.test_config
    bundle = Bundle.parse_raw(test_config.response.body)
    assert len(bundle.entry) == count, bundle
    assert bundle.total == count, bundle


@then("the Bundle contains an Entry with the below values for {template_name} template")
def the_response_contains_the_template_with_values(
    context: Context, template_name: str
):
    test_config: TestConfig = context.test_config
    bundle = test_config.response.dict

    document_references = [entry["resource"] for entry in bundle["entry"]]
    template = test_config.templates[template_name]
    rendered_template = template.render_fhir(table=context.table)
    fhir_json = json.loads(rendered_template)
    assert fhir_json in document_references, document_references


@then('the response contains the message "{message}"')
def assert_error_message(context: Context, message: str):
    test_config: TestConfig = context.test_config
    actual_message = test_config.response.dict["message"]
    assert actual_message == message, asdict(test_config.response)


@then('the response contains error message "{message}"')
def assert_error_message(context: Context, message: str):
    test_config: TestConfig = context.test_config
    assert test_config.response.error == message, asdict(test_config.response)


@then("the response is the policy from {template_name} template")
def response_contains_correct_policy(context: Context, template_name: str):
    test_config: TestConfig = context.test_config
    template = test_config.templates[template_name]
    template_policy = json.loads(template.render(table=context.table))
    template_policy = _populate_template_policy_from_request_headers(
        test_config=test_config, template_policy=template_policy
    )
    assert template_policy == test_config.response.dict, test_config.response.dict


def _remove_outer_brackets(text: str):
    return text[1:-1]


def _populate_template_policy_from_request_headers(
    test_config: TestConfig, template_policy: str
):
    """
    Replaces constants in the template i.e. <things-like-this>
    with values set in headers, for example <x-correlation-id>
    """
    client_rp_details = test_config.request.client_rp_details.dict(by_alias=True)
    headers = {**test_config.request.headers, **client_rp_details}

    template_policy["context"] = {
        k: headers[k] if k in headers and f"<{k}>" == v else v
        for k, v in template_policy["context"].items()
    }

    principal_id_keyword = template_policy["principalId"]
    if principal_id_keyword != "null":
        principal_id_keyword = _remove_outer_brackets(template_policy["principalId"])
        template_policy["principalId"] = headers[principal_id_keyword]

    return template_policy
