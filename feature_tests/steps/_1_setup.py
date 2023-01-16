import json

from behave import given as behave_given
from behave.runner import Context
from nrlf.core.constants import Source
from nrlf.core.model import DocumentPointer
from nrlf.core.transform import create_document_pointer_from_fhir_json, make_timestamp
from nrlf.producer.fhir.r4.model import Bundle, BundleEntry, DocumentReference
from nrlf.producer.fhir.r4.strict_model import (
    DocumentReference as StrictDocumentReference,
)

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
    "an invalid Document Pointer exists in the system with the below values for {template_name} template"
)
def given_invalid_document_pointer_exists(context: Context, template_name: str):
    test_config: TestConfig = context.test_config
    template = test_config.templates[template_name]
    rendered_template = template.render(
        context.table, fhir_type=FhirType.DocumentReference
    )
    core_model = _invalidate_document_pointer_object(rendered_template)

    table_name = test_config.environment_prefix + core_model.kebab()
    test_config.dynamodb_client.put_item(TableName=table_name, Item=core_model.dict())


def _invalidate_document_pointer_object(rendered_template):
    modify_template = json.loads(rendered_template)
    author = modify_template["author"]
    del modify_template["author"]

    core_model = _create_invalid_document_pointer_from_fhir_json(
        fhir_json=json.loads(json.dumps(modify_template)),
        api_version=int(DEFAULT_VERSION),
    )

    document = json.loads(core_model.document.__root__)
    document["author"] = author
    core_model.document = {"S": json.dumps(document)}
    return core_model


def _create_invalid_document_pointer_from_fhir_json(
    fhir_json: dict,
    api_version: int,
    source: Source = Source.NRLF,
    **kwargs,
) -> DocumentPointer:
    fhir_model = _create_fhir_model_from_fhir_json(fhir_json=fhir_json)
    core_model = DocumentPointer(
        id=fhir_model.id,
        nhs_number=fhir_model.subject.identifier.value,
        type=fhir_model.type,
        version=api_version,
        document=json.dumps(fhir_json),
        source=source.value,
        created_on=kwargs.pop("created_on", make_timestamp()),
        **kwargs,
    )
    return core_model


def _create_fhir_model_from_fhir_json(fhir_json: dict) -> StrictDocumentReference:
    DocumentReference(**fhir_json)
    fhir_strict_model = StrictDocumentReference(**fhir_json)
    return fhir_strict_model
