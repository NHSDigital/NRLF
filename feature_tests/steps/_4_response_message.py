import json
from dataclasses import asdict

from behave.runner import Context

from feature_tests.common.constants import FhirType
from feature_tests.common.decorators import then
from feature_tests.common.models import TestConfig
from nrlf.producer.fhir.r4.strict_model import Bundle


@then(
    "the response is {a_or_an} {fhir_type} according to the {template_name} template with the below values"
)
def the_response_is_the_template_with_values(
    context: Context, a_or_an: str, fhir_type: str, template_name: str
):
    try:
        fhir_type = FhirType._member_map_[fhir_type]
    except KeyError:
        raise ValueError(
            f"{fhir_type} is not one of {FhirType._member_names_}"
        ) from None

    test_config: TestConfig = context.test_config
    rendered = test_config.templates[template_name].render(
        table=context.table, fhir_type=fhir_type
    )

    if fhir_type is FhirType.OperationOutcome:
        id = test_config.response.dict["id"]
        rendered = rendered.replace("<identifier>", id)

    actual = test_config.response.dict
    expected = json.loads(rendered)

    assert actual == expected, {
        "actual": actual,
        "expected": asdict(test_config.response),
    }


@then("the response is a Bundle with {count:d} entries")
def producer_search_document_pointers(context: Context, count: int):
    test_config: TestConfig = context.test_config
    bundle = Bundle.parse_raw(test_config.response.body)
    assert len(bundle.entry) == count, bundle.dict()
    assert bundle.total == count, bundle.dict()


@then("the Bundle contains an Entry with the below values for {template_name} template")
def the_response_contains_the_template_with_values(
    context: Context, template_name: str
):
    test_config: TestConfig = context.test_config
    bundle = test_config.response.dict

    document_references = [entry["resource"] for entry in bundle["entry"]]
    template = test_config.templates[template_name]
    rendered_template = template.render(
        table=context.table, fhir_type=FhirType.DocumentReference
    )
    fhir_json = json.loads(rendered_template)
    assert fhir_json in document_references, document_references


@then("the response is the policy from {template_name} template")
def response_contains_correct_policy(context: Context, template_name: str):
    test_config: TestConfig = context.test_config
    template = test_config.templates[template_name]
    template_policy = json.loads(template.render(table=context.table))
    response = test_config.response.dict

    # principalId is generated from the transaction id, so don't test this
    template_policy.pop("principalId")
    response.pop("principalId")

    assert template_policy == response, response
