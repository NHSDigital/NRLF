import json

from behave import given as behave_given
from behave.runner import Context
from nrlf.core.model import DocumentPointer
from nrlf.core.transform import create_document_pointer_from_fhir_json

from feature_tests.common.config_setup import (
    mock_local_auth,
    register_application,
    request_setup,
)
from feature_tests.common.constants import DEFAULT_VERSION, TestMode
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
    '{actor_type} "{actor}" {has_hasnt} authorisation headers for application "{app_name}" (ID "{app_id}")'
)
def authorised_for_application(
    context: Context,
    actor_type: str,
    actor: str,
    has_hasnt: str,
    app_name: str,
    app_id: str,
):
    test_config: TestConfig = context.test_config
    if has_hasnt == "has":
        test_config.request.set_auth_headers(
            org_id=test_config.actor_context.org_id, app_id=app_id, app_name=app_name
        )
    elif has_hasnt != "does not have":
        raise ValueError(f"'{has_hasnt}' must be one of ['has', 'does not have']")

    if test_config.mode is TestMode.LOCAL_TEST:
        mock_local_auth(
            test_config=test_config, org_id=test_config.actor_context.org_id
        )


@given(
    '{actor_type} "{actor}" is registered in the system for application "{app_name}" (ID "{app_id}") for document types'
)
def registered_in_system(
    context: Context, actor_type: str, actor: str, app_name: str, app_id: str
):
    test_config: TestConfig = context.test_config
    register_application(
        context=context,
        org_id=test_config.actor_context.org_id,
        app_name=app_name,
        app_id=app_id,
    )


@given(
    '{actor_type} "{actor}" is not registered in the system for application "{app_name}" (ID "{app_id}")'
)
def registered_in_system(
    context: Context, actor_type: str, actor: str, app_name: str, app_id: str
):
    pass


@given(
    "a Document Pointer exists in the system with the below values for {template_name} template"
)
def given_document_pointer_exists(context: Context, template_name: str):
    test_config: TestConfig = context.test_config
    template = test_config.templates[template_name]
    rendered_template = template.render_fhir(context.table)
    core_model = create_document_pointer_from_fhir_json(
        fhir_json=json.loads(rendered_template), api_version=int(DEFAULT_VERSION)
    )
    test_config.repositories[DocumentPointer].create(core_model)
