from behave import *  # noqa
from behave.runner import Context

from tests.features.utils.api_client import ConsumerClient, ProducerClient
from tests.features.utils.data import (
    create_test_document_reference,
    create_test_document_reference_with_defaults,
)


@when("consumer '{ods_code}' counts DocumentReferences with parameters")
def consumer_count_document_references_step(context: Context, ods_code: str):
    client = ConsumerClient.from_context(context, ods_code)

    if not context.table:
        raise ValueError("No count query table provided")

    items = {row["parameter"]: row["value"] for row in context.table}
    context.response = client.count(items)


@when("consumer '{ods_code}' searches for DocumentReferences with parameters")
def consumer_search_document_reference_step(context: Context, ods_code: str):
    client = ConsumerClient.from_context(context, ods_code)

    if not context.table:
        raise ValueError("No search query table provided")

    items = {row["parameter"]: row["value"] for row in context.table}

    subject = items.pop("subject", None)
    custodian = items.pop("custodian", None)
    pointer_type = items.pop("pointer_type", None)

    context.response = client.search(
        nhs_number=subject,
        custodian=custodian,
        pointer_type=pointer_type,
        extra_params=items,
    )


@when(
    "consumer '{ods_code}' searches for DocumentReferences using POST with request body"
)
def consumer_search_post_document_reference_step(context: Context, ods_code: str):
    client = ConsumerClient.from_context(context, ods_code)

    if not context.table:
        raise ValueError("No search query table provided")

    items = {row["key"]: row["value"] for row in context.table}

    subject = items.pop("subject", None)
    custodian = items.pop("custodian", None)
    pointer_type = items.pop("pointer_type", None)

    context.response = client.search_post(
        nhs_number=subject,
        custodian=custodian,
        pointer_type=pointer_type,
        extra_fields=items,
    )


@when("consumer '{ods_code}' reads a DocumentReference with ID '{doc_ref_id}'")
def consumer_read_document_reference_step(
    context: Context, ods_code: str, doc_ref_id: str
):
    client = ConsumerClient.from_context(context, ods_code)
    context.response = client.read(doc_ref_id)


@when("producer '{ods_code}' creates a DocumentReference with values")
def create_post_document_reference_step(context: Context, ods_code: str):
    client = ProducerClient.from_context(context, ods_code)

    if not context.table:
        raise ValueError("No document reference data table provided")

    items = {row["property"]: row["value"] for row in context.table}

    doc_ref = create_test_document_reference(items)
    context.response = client.create(doc_ref.dict(exclude_none=True))

    if context.response.status_code == 201:
        doc_ref_id = context.response.headers["Location"].split("/")[-1]
        doc_ref_id.replace(
            "|", "."
        )  # NRL-766 define and resolve custodian suffix behaviour
        context.add_cleanup(lambda: context.repository.delete_by_id(doc_ref_id))


@when(
    "producer 'TSTCUS' requests creation of a DocumentReference with default test values except '{section}' is"
)
def create_post_body_step(context: Context, section: str):
    client = ProducerClient.from_context(context, "TSTCUS")

    if not context.text:
        raise ValueError("No document reference text snippet provided")

    doc_ref = create_test_document_reference_with_defaults(section, context.text)
    context.response = client.create_text(doc_ref)

    if context.response.status_code == 201:
        doc_ref_id = context.response.headers["Location"].split("/")[-1]
        doc_ref_id.replace(
            "|", "."
        )  # NRL-766 define and resolve custodian suffix behaviour
        context.add_cleanup(lambda: context.repository.delete_by_id(doc_ref_id))


@when("producer '{ods_code}' upserts a DocumentReference with values")
def create_put_document_reference_step(context: Context, ods_code: str):
    client = ProducerClient.from_context(context, ods_code)

    if not context.table:
        raise ValueError("No document reference data table provided")

    items = {row["property"]: row["value"] for row in context.table}

    doc_ref = create_test_document_reference(items)
    context.response = client.upsert(doc_ref.dict(exclude_none=True))


@when(
    "producer '{ods_code}' requests to delete DocumentReference with id '{doc_ref_id}'"
)
def delete_document_reference_step(context: Context, ods_code: str, doc_ref_id: str):
    client = ProducerClient.from_context(context, ods_code)
    context.response = client.delete(doc_ref_id)


@when("producer '{ods_code}' reads a DocumentReference with ID '{doc_ref_id}'")
def producer_read_document_reference_step(
    context: Context, ods_code: str, doc_ref_id: str
):
    client = ProducerClient.from_context(context, ods_code)
    context.response = client.read(doc_ref_id)


@when("producer '{ods_code}' searches for DocumentReferences with parameters")
def producer_search_document_reference_step(context: Context, ods_code: str):
    client = ProducerClient.from_context(context, ods_code)

    if not context.table:
        raise ValueError("No search query table provided")

    items = {row["parameter"]: row["value"] for row in context.table}

    subject = items.pop("subject", None)
    pointer_type = items.pop("pointer_type", None)

    context.response = client.search(
        nhs_number=subject,
        pointer_type=pointer_type,
        extra_params=items,
    )
