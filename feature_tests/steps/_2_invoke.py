import json

from feature_tests.common.constants import FhirType
from feature_tests.common.decorators import when
from feature_tests.common.models import Context, TestConfig
from feature_tests.common.utils import table_as_dict


@when(
    '{actor_type} "{actor}" creates a Document Reference from {template_name} template',
    action="create",
)
def producer_create_document_pointer_from_template(
    context: Context, actor_type: str, actor: str, template_name: str
):
    test_config: TestConfig = context.test_config
    rendered_template = test_config.rendered_templates.get(template_name)
    if not rendered_template:
        template = test_config.templates[template_name]
        rendered_template = template.render(
            context.table, fhir_type=FhirType.DocumentReference
        )
    test_config.response = test_config.request.invoke(body=rendered_template)


@when(
    '{actor_type} "{actor}" creates a Document Reference with bad json',
    action="create",
)
def producer_create_document_pointer_from_bad_json(
    context: Context,
    actor_type: str,
    actor: str,
):
    test_config: TestConfig = context.test_config
    test_config.response = test_config.request.invoke(body=context.text)


@when('{actor_type} "{actor}" {action} an existing Document Reference "{id}"')
def producer_reads_or_deletes_existing_document_reference(
    context: Context, actor_type: str, actor: str, action: str, id: str
):
    test_config: TestConfig = context.test_config
    test_config.response = test_config.request.invoke(path_params={"id": id})


@when(
    '{actor_type} "{actor}" searches for Document References with query parameters',
    action="search",
)
def producer_searches_existing_document_reference(
    context: Context, actor_type: str, actor: str
):
    test_config: TestConfig = context.test_config

    query_params = table_as_dict(table=context.table)
    test_config.requestParams = query_params
    test_config.response = test_config.request.invoke(query_params=query_params)


@when(
    '{actor_type} "{actor}" counts Document References with query parameters',
    action="count",
)
def producer_searches_existing_document_reference(
    context: Context, actor_type: str, actor: str
):
    test_config: TestConfig = context.test_config

    query_params = table_as_dict(table=context.table)
    test_config.requestParams = query_params
    test_config.response = test_config.request.invoke(query_params=query_params)


@when(
    '{actor_type} "{actor}" searches for the next page',
    action="search",
)
def producer_searches_existing_document_reference_next_page(
    context: Context, actor_type: str, actor: str
):
    test_config: TestConfig = context.test_config
    bundle = test_config.response.dict
    next_page_token = bundle["meta"]["tag"][0]["code"]
    test_config.requestParams["next-page-token"] = next_page_token

    test_config.response = test_config.request.invoke(
        query_params=test_config.requestParams
    )


@when(
    '{actor_type} "{actor}" searches by POST for Document References with body parameters',
    action="searchPost",
)
def search_document_pointers(context: Context, actor_type: str, actor: str):
    test_config: TestConfig = context.test_config
    table_params = table_as_dict(table=context.table)
    test_config.requestParams = table_params
    body = json.dumps(table_params)
    test_config.response = test_config.request.invoke(body=body)


@when(
    '{actor_type} "{actor}" searches by POST for the next page',
    action="searchPost",
)
def search_document_pointers_next_page(context: Context, actor_type: str, actor: str):
    test_config: TestConfig = context.test_config
    bundle = test_config.response.dict
    next_page_token = bundle["meta"]["tag"][0]["code"]

    test_config.requestParams["next-page-token"] = next_page_token

    body = json.dumps(test_config.requestParams)
    test_config.response = test_config.request.invoke(body=body)


@when(
    '{actor_type} "{actor}" updates Document Reference "{id}" from {template_name} template',
    action="update",
)
def producer_update_document_pointer_from_template(
    context: Context, actor_type: str, actor: str, id: str, template_name: str
):
    test_config: TestConfig = context.test_config
    body = test_config.templates[template_name].render(
        table=context.table, fhir_type=FhirType.DocumentReference
    )
    test_config.response = test_config.request.invoke(body=body, path_params={"id": id})


@when('{actor_type} "{actor}" has their authorisation evaluated', action="authoriser")
def request_contains_correct_headers(context: Context, actor_type: str, actor: str):
    test_config: TestConfig = context.test_config
    test_config.response = test_config.request.invoke()
