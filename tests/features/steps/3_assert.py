import json

from behave import *  # noqa
from behave.runner import Context

from nrlf.producer.fhir.r4.model import Bundle, DocumentReference, OperationOutcome


def format_error(
    message: str, expected: str | None, actual: str | None, response: str | None
):
    message = f"{message}\n\nExpected: {expected}\nActual: {actual}"
    if response:
        message += f"\n\nResponse body:\n{response}"

    return message


@then("the response status code is {status_code}")
def assert_response_status_code_step(context: Context, status_code: str):
    assert context.response.status_code == int(status_code), format_error(
        "Status code does not match",
        status_code,
        str(context.response.status_code),
        context.response.text,
    )


@then("the response does not contain the key '{key}'")
def assert_response_no_key_in_response_step(context: Context, key: str):
    assert key not in context.response.json(), f"Key {key} found in response"


@then("the response is a {bundle_type} Bundle")
def assert_bundle_step(context: Context, bundle_type: str):
    body = context.response.json()

    assert body["resourceType"] == "Bundle", format_error(
        "Unexpected resourceType",
        "Bundle",
        body["resourceType"],
        context.response.text,
    )
    assert body["type"] == bundle_type, format_error(
        "Unexpected type",
        bundle_type,
        body["type"],
        context.response.text,
    )

    context.bundle = Bundle.parse_obj(body)


@then("the Bundle has a total of {total}")
def assert_bundle_total_step(context: Context, total: str):
    assert (
        context.bundle is not None
    ), "The Bundle has not been yet parsed from the response"
    assert context.bundle.total == int(total), format_error(
        "Unexpected Bundle total",
        total,
        str(context.bundle.total),
        context.response.text,
    )


@then("the Bundle has a self link matching '{rel_url}'")
def assert_bundle_self(context: Context, rel_url: str):
    assert (
        context.bundle is not None
    ), "The Bundle has not yet been parsed from the response"
    assert context.bundle.link is not None, format_error(
        "No links present in the Bundle",
        f"{context.base_url}{rel_url}",
        "None",
        context.response.text,
    )

    assert len(context.bundle.link) == 1, format_error(
        "The Bundle's link array should contain a single item if no pagination is used",
        "1 entry",
        f"{len(context.bundle.link)} entries",
        context.response.text,
    )

    link_entry = context.bundle.link[0].dict(exclude_none=True)
    assert link_entry.get("relation") == "self", format_error(
        "Link should specify a 'self' type relation",
        "self",
        link_entry.get("relation"),
        context.response.text,
    )

    actual_url_params = link_entry.get("url").split("consumer/FHIR/R4/")[-1]
    assert actual_url_params == rel_url, format_error(
        "Link url does not specify the search parameters expected",
        rel_url,
        actual_url_params,
        context.response.text,
    )


@then("the Bundle has {num_entries} entry")
@then("the Bundle has {num_entries} entries")
def assert_bundle_entries_step(context: Context, num_entries: str):
    assert (
        context.bundle is not None
    ), "The Bundle has not been yet parsed from the response"
    assert len(context.bundle.entry) == int(num_entries), format_error(
        "Unexpected number of Bundle entries",
        num_entries,
        str(len(context.bundle.entry)),
        context.response.text,
    )


def assert_document_reference_matches_value(
    context: Context, doc_ref: dict | DocumentReference, items: dict
):
    """
    Asserts that the given document reference matches the expected values.

    Args:
        context (Context): The context object.
        doc_ref (dict): The actual document reference.
        items (dict): The expected values for the document reference.

    Raises:
        AssertionError: If any of the document reference values do not match the expected values.
    """
    if isinstance(doc_ref, dict):
        doc_ref = DocumentReference.parse_obj(doc_ref)

    assert doc_ref.id == items["id"], format_error(
        "DocumentReference ID does not match",
        items["id"],
        doc_ref.id,
        context.response.json(),
    )

    if status := items.get("status"):
        assert doc_ref.status == status, format_error(
            "DocumentReference status does not match",
            status,
            doc_ref.status,
            context.response.json(),
        )

    if type_code := items.get("type"):
        assert doc_ref.type.coding[0].code == type_code, format_error(
            "DocumentReference type does not match",
            type_code,
            doc_ref.type.coding[0].code,
            context.response.json(),
        )

    if category := items.get("category"):
        assert doc_ref.category[0].coding[0].code == category, format_error(
            "DocumentReference custodian does not match",
            category,
            doc_ref.category[0].coding[0].code,
            context.response.json(),
        )

    if subject := items.get("subject"):
        assert doc_ref.subject.identifier.value == subject, format_error(
            "DocumentReference subject does not match",
            subject,
            doc_ref.subject.identifier.value,
            context.response.json(),
        )

    if custodian := items.get("custodian"):
        assert doc_ref.custodian.identifier.value == custodian, format_error(
            "DocumentReference custodian does not match",
            custodian,
            doc_ref.custodian.identifier.value,
            context.response.json(),
        )

    if author := items.get("author"):
        assert doc_ref.author[0].identifier.value == author, format_error(
            "DocumentReference author does not match",
            author,
            doc_ref.author[0].identifier.value,
            context.response.json(),
        )

    if content_type := items.get("contentType"):
        assert doc_ref.content[0].attachment.contentType == content_type, format_error(
            "DocumentReference content type does not match",
            content_type,
            doc_ref.content[0].attachment.contentType,
            context.response.json(),
        )

    if url := items.get("url"):
        assert doc_ref.content[0].attachment.url == url, format_error(
            "DocumentReference URL does not match",
            url,
            doc_ref.content[0].attachment.url,
            context.response.json(),
        )


@then("the Bundle contains an DocumentReference with values")
def assert_bundle_contains_documentreference_values_step(context: Context):
    if not context.table:
        raise ValueError("No DocumentReference table provided")

    items = {row["property"]: row["value"] for row in context.table}
    if not items.get("id"):
        raise ValueError("No id provided in the table")

    for entry in context.bundle.entry:
        if entry.resource.id != items["id"]:
            continue

        return assert_document_reference_matches_value(context, entry.resource, items)

    raise AssertionError(
        f"DocumentReference with id {items['id']} not found in the response\n\nFull response:\n{json.dumps(context.response.json(), indent=2)}"
    )


@then("the Bundle does not contain a DocumentReference with ID '{doc_ref_id}'")
def assert_bundle_does_not_contain_doc_ref_step(context: Context, doc_ref_id: str):
    for entry in context.bundle.entry:
        assert (
            entry.resource.id != doc_ref_id
        ), f"DocumentReference with ID {doc_ref_id} found in the response"


@then("the response is an OperationOutcome with {num_issues} issue")
@then("the response is an OperationOutcome with {num_issues} issues")
def assert_response_operation_outcome_step(context: Context, num_issues: str):
    body = context.response.json()
    assert body["resourceType"] == "OperationOutcome"
    assert len(body["issue"]) == int(num_issues)

    context.operation_outcome = OperationOutcome.parse_obj(body)


@then("the OperationOutcome contains the issue")
def assert_response_operation_outcome_issue(context: Context):
    if not context.text:
        raise ValueError("No issue JSON provided")

    try:
        content = json.loads(context.text)
    except:
        raise ValueError("Invalid JSON provided")

    for issue in context.operation_outcome.issue:
        if issue.dict(exclude_none=True) == content:
            return

    raise ValueError(
        f"Could not find issue in response:\n\nFull Response:\n{json.dumps(context.response.json(), indent=2)}\n\nExpected Issue:\n{json.dumps(content, indent=2)}"
    )


@then("the response is a DocumentReference with JSON value")
def assert_response_document_reference_step(context: Context):
    if not context.text:
        raise ValueError("No DocumentReference JSON provided")

    try:
        content = json.loads(context.text)
    except:
        raise ValueError("Invalid JSON provided")

    assert context.response.json()["resourceType"] == "DocumentReference", format_error(
        "Response is not a DocumentReference",
        "DocumentReference",
        context.response.json()["resourceType"],
        context.response.text,
    )

    assert context.response.json() == content, format_error(
        "DocumentReference does not match",
        json.dumps(content, indent=2),
        json.dumps(context.response.json(), indent=2),
        context.response.text,
    )


@then("the {header_name} header is '{header_value}'")
def assert_header(context: Context, header_name: str, header_value: str):
    assert context.response.headers.get(header_name) == header_value, format_error(
        f"Header {header_name} does not match",
        header_value,
        context.response.headers.get(header_name),
        context.response.text,
    )


@then("the response has a {header_name} header")
def assert_location_header(context: Context, header_name: str):
    generated_id = context.response.headers.get(header_name)

    # check there is a location header
    assert generated_id is not None, format_error(
        f"Missing {header_name} header",
        None,
        None,
        context.response.text,
    )
    context.pointer_id = generated_id


@then("the {header_name} header starts with '{starts_with}'")
def assert_header_starts_with(context: Context, header_name: str, starts_with: str):
    header_value = context.response.headers.get(header_name)
    assert header_value.startswith(starts_with), format_error(
        f"Header {header_name} does not start with expected value",
        starts_with,
        header_value,
        context.response.text,
    )


@then("the resource in the Location header exists with values")
def assert_resource_in_location_header_exists_with_values(context: Context):
    location = context.response.headers.get("Location")

    assert location.startswith(
        "/nrl-producer-api/FHIR/R4/DocumentReference/"
    ), format_error(
        "Unexpected Location header",
        "/nrl-producer-api/FHIR/R4/DocumentReference/",
        location,
        context.response.text,
    )

    resource_id = location.split("/")[-1]
    resource = context.repository.get_by_id(resource_id)
    assert resource is not None, format_error(
        "Resource does not exist",
        resource_id,
        None,
        context.response.text,
    )

    if not context.table:
        raise ValueError("No DocumentReference table provided")

    items = {row["property"]: row["value"] for row in context.table}
    items["id"] = resource_id

    assert_document_reference_matches_value(
        context, DocumentReference.parse_raw(resource.document), items
    )
