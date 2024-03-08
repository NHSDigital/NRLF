import json
from datetime import date

from behave import given as behave_given

from data_contracts.deploy_contracts.deploy_contracts import sync_contracts
from feature_tests.common.config_setup import register_application, request_setup
from feature_tests.common.constants import DEFAULT_VERSION, WITH_WITHOUT_ANY, FhirType
from feature_tests.common.decorators import given
from feature_tests.common.models import Context, Template, TestConfig
from nrlf.core_pipeline.constants import CONNECTION_METADATA, DbPrefix
from nrlf.core_pipeline.model import Contract, DocumentPointer, key
from nrlf.core_pipeline.transform import create_document_pointer_from_fhir_json
from nrlf.core_pipeline.validators import json_loads, split_custodian_id


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


def _registered_in_system(
    context: Context,
    actor_type: str,
    actor: str,
    app_name: str,
    app_id: str,
    with_without_any: str,
    enable_s3_for_permissions: bool = False,
):
    test_config: TestConfig = context.test_config
    if with_without_any not in WITH_WITHOUT_ANY:
        raise ValueError(f"Term '{with_without_any}' must be one of {WITH_WITHOUT_ANY}")

    pointer_types = (
        [f'{row["system"]}|{row["value"]}' for row in context.table]
        if with_without_any == "with"
        else []
    )

    org_id, org_id_extension = split_custodian_id(test_config.actor_context.org_id)

    register_application(
        context=context,
        org_id=org_id,
        org_id_extension=org_id_extension,
        app_name=app_name,
        app_id=app_id,
        pointer_types=pointer_types,
        enable_s3_for_permissions=enable_s3_for_permissions,
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
    _registered_in_system(
        context=context,
        actor_type=actor_type,
        actor=actor,
        app_name=app_name,
        app_id=app_id,
        with_without_any=with_without_any,
        enable_s3_for_permissions=False,
    )


@given(
    '{actor_type} "{actor}" is registered in the system for application "{app_name}" (ID "{app_id}") {with_without_any} pointer types stored in NRLF'
)
def registered_in_system(
    context: Context,
    actor_type: str,
    actor: str,
    app_name: str,
    app_id: str,
    with_without_any: str,
):
    _registered_in_system(
        context=context,
        actor_type=actor_type,
        actor=actor,
        app_name=app_name,
        app_id=app_id,
        with_without_any=with_without_any,
        enable_s3_for_permissions=True,
    )


@given('{actor_type} "{actor}" has the permission "{permission}"')
def has_permissions(
    context: Context,
    actor_type: str,
    actor: str,
    permission: str,
):
    test_config: TestConfig = context.test_config
    existing_headers = json_loads(test_config.request.headers[CONNECTION_METADATA])
    existing_headers["nrl.permissions"] = [permission]
    test_config.request.headers[CONNECTION_METADATA] = json.dumps(existing_headers)


@given('{actor_type} "{actor}" has the permissions')
def has_permissions(
    context: Context,
    actor_type: str,
    actor: str,
):
    test_config: TestConfig = context.test_config
    existing_headers = json_loads(test_config.request.headers[CONNECTION_METADATA])

    permissions = [row["permission"] for row in context.table]

    existing_headers["nrl.permissions"] = permissions
    test_config.request.headers[CONNECTION_METADATA] = json.dumps(existing_headers)


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
        fhir_json=json_loads(rendered_template), api_version=int(DEFAULT_VERSION)
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
                new_identifier = identifier[:-6] + str(documents_created).zfill(6)
                row.cells[1] = new_identifier

        rendered_template = template.render(
            context.table, fhir_type=FhirType.DocumentReference
        )
        core_model = create_document_pointer_from_fhir_json(
            fhir_json=json_loads(rendered_template), api_version=int(DEFAULT_VERSION)
        )
        test_config.repositories[DocumentPointer].create(core_model)
        documents_created += 1


@given("a Data Contract is registered in the system")
def data_contract_registered_in_the_system(context: Context):
    test_config: TestConfig = context.test_config
    contract_kwargs = {row["property"]: row["value"] for row in context.table}

    json_schema = json_loads(
        test_config.templates[contract_kwargs.pop("json_schema_template")].raw
    )
    inverse_version = contract_kwargs.pop("inverse_version")
    contract = Contract(
        pk=key(DbPrefix.Contract, contract_kwargs["system"], contract_kwargs["value"]),
        sk=key(DbPrefix.Version, inverse_version, contract_kwargs["name"]),
        json_schema=json_schema,
        **contract_kwargs,
    )
    test_config.repositories[Contract].create(item=contract)


@given("the Data Contracts are loaded from the database")
def load_data_contracts_from_database(context: Context):
    test_config: TestConfig = context.test_config
    sync_contracts(
        test_config.repositories[Contract], today=date(year=2000, month=1, day=1)
    )
