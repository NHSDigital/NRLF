import json

from behave import given as behave_given
from behave.runner import Context
from nrlf.core.model import DocumentPointer
from nrlf.core.transform import create_document_pointer_from_fhir_json

from feature_tests.common.config_setup import register_application, request_setup
from feature_tests.common.constants import DEFAULT_VERSION, WITH_WITHOUT_ANY, FhirType
from feature_tests.common.decorators import given
from feature_tests.common.models import Template, TestConfig


@behave_given("template {template_name}")
def create_template_document(context: Context, template_name: str):
    test_config: TestConfig = context.test_config
    test_config.templates[template_name] = Template(raw=context.text)


@behave_given(
    '{actor_type} "{actor}" (Organisation ID "{org_id}") is requesting to {action} Document Pointers'
)
def given_permissions_for_types(
    context: Context, actor_type: str, actor: str, org_id: str, action: str
):
    if "Authoriser" in context.scenario.name:
        action = "authoriser"

    test_config: TestConfig = context.test_config
    test_config.request = request_setup(
        context=context,
        actor=actor,
        org_id=org_id,
        actor_type=actor_type,
        action=action,
    )


@given(
    '{actor_type} "{actor}" is registered in the system for application "{app_name}" (ID "{app_id}") {with_without_any} pointer types'
)
def registered_in_system(
    context: Context,
    actor_type: str,
    actor: str,
    app_name: str,
    app_id: str,
    with_without_any: str,
):
    test_config: TestConfig = context.test_config
    if with_without_any not in WITH_WITHOUT_ANY:
        raise ValueError(f"Term '{with_without_any}' must be one of {WITH_WITHOUT_ANY}")

    pointer_types = (
        [f'{row["system"]}|{row["value"]}' for row in context.table]
        if with_without_any == "with"
        else []
    )
    register_application(
        context=context,
        org_id=test_config.actor_context.org_id,
        app_name=app_name,
        app_id=app_id,
        pointer_types=pointer_types,
    )


@given(
    "a Document Pointer exists in the system with the below values for {template_name} template"
)
def given_document_pointer_exists(context: Context, template_name: str):
    test_config: TestConfig = context.test_config
    template = test_config.templates[template_name]
    rendered_template = template.render(
        context.table, fhir_type=FhirType.DocumentReference
    )
    core_model = create_document_pointer_from_fhir_json(
        fhir_json=json.loads(rendered_template), api_version=int(DEFAULT_VERSION)
    )
    test_config.repositories[DocumentPointer].create(core_model)


@given(
    "{count:d} Document Pointers exists in the system with the below values for {template_name} template"
)
def given_document_pointer_exists(context: Context, count: int, template_name: str):
    test_config: TestConfig = context.test_config
    template = test_config.templates[template_name]

    documents_created = 0
    while documents_created < count:
        for row in context.table:
            if row["property"] == "identifier":
                identifier = row["value"]
                new_identifier = identifier[:-2] + str(documents_created).zfill(2)
                row.cells[1] = new_identifier

        rendered_template = template.render(
            context.table, fhir_type=FhirType.DocumentReference
        )
        core_model = create_document_pointer_from_fhir_json(
            fhir_json=json.loads(rendered_template), api_version=int(DEFAULT_VERSION)
        )
        test_config.repositories[DocumentPointer].create(core_model)
        documents_created += 1
