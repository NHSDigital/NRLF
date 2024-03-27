import json

import boto3
from behave import *  # noqa
from behave.runner import Context
from pydantic import BaseModel

from nrlf.core.dynamodb.model import DocumentPointer
from nrlf.producer.fhir.r4.model import (
    Attachment,
    CodeableConcept,
    Coding,
    DocumentReference,
    DocumentReferenceContent,
    Identifier,
    Reference,
)
from tests.features.utils.api_client import (
    ClientConfig,
    ConnectionMetadata,
    ConsumerClient,
)


class Application(BaseModel):
    app_id: str = "UNSET"
    app_name: str = "UNSET"
    enable_s3_permissions_lookup: bool = False
    permissions: dict[str, list[str]] = {}

    def add_permissions(self, ods_code: str, permissions: list[str]):
        self.permissions[ods_code] = permissions


@given("the application '{app_name}' (ID '{app_id}') is registered to access the API")
def register_application_step(context: Context, app_name: str, app_id: str):
    context.application = Application(app_id=app_id, app_name=app_name)


@given("the application is configured to lookup permissions from S3")
def configure_application_permissions_lookup_step(context: Context):
    context.application.enable_s3_permissions_lookup = True


@given(
    "the organisation '{org_name}' (ODS code '{ods_code}') is authorised to access pointer types"
)
def register_org_permissions_step(context: Context, org_name: str, ods_code: str):
    if not context.table:
        raise ValueError("No permissions table provided")

    pointer_types = [f"{system}|{value}" for system, value in context.table]
    context.application.add_permissions(ods_code, pointer_types)


@given(
    "the organisation '{org_name}' (ODS code '{ods_code}') is authorised in S3 to access pointer types"
)
def register_org_permissions_s3_step(context: Context, org_name: str, ods_code: str):
    if not context.table:
        raise ValueError("No permissions table provided")

    pointer_types = [f"{system}|{value}" for system, value in context.table]
    bucket = f"nhsd-nrlf--{context.env}--authorization-store"
    key = f"{context.application.app_id}/{ods_code}.json"

    s3_client = boto3.client("s3")
    s3_client.put_object(Bucket=bucket, Key=key, Body=json.dumps(pointer_types))
    context.add_cleanup(lambda: s3_client.delete_object(Bucket=bucket, Key=key))


@given("a DocumentReference resource exists with values")
def create_document_reference_step(context: Context):
    if not context.table:
        raise ValueError("No DocumentReference table provided")

    items = {row["property"]: row["value"] for row in context.table}
    base_doc_ref = DocumentReference(
        resourceType="DocumentReference",
        id=items["id"],
        status=items["status"],
        content=[
            DocumentReferenceContent(
                attachment=Attachment(
                    contentType=items["contentType"], url=items["url"]
                )
            )
        ],
    )

    if items.get("type"):
        base_doc_ref.type = CodeableConcept(
            coding=[Coding(system="http://snomed.info/sct", code=items["type"])]
        )

    if items.get("subject"):
        base_doc_ref.subject = Reference(
            identifier=Identifier(
                system="https://fhir.nhs.uk/Id/nhs-number", value=items["subject"]
            )
        )

    if items.get("custodian"):
        base_doc_ref.custodian = Reference(
            identifier=Identifier(
                system="https://fhir.nhs.uk/Id/ods-organization-code",
                value=items["custodian"],
            )
        )

    doc_pointer = DocumentPointer.from_document_reference(base_doc_ref)
    context.repository.create(doc_pointer)
    context.add_cleanup(lambda: context.repository.delete(doc_pointer))


@given("no pointer types are configured in S3 for the organisation '{ods_code}'")
def no_pointer_types_configured_step(context: Context, ods_code: str):
    pass


@when(
    "the organisation '{ods_code}' requests to count DocumentReferences with parameters"
)
def count_document_references_step(context: Context, ods_code: str):
    client = ConsumerClient(
        config=ClientConfig(
            base_url=context.base_url,
            client_cert=context.client_cert,
            connection_metadata=ConnectionMetadata.parse_obj(
                {
                    "nrl.pointer-types": context.application.permissions.get(
                        ods_code, []
                    ),
                    "nrl.ods-code": ods_code,
                    "nrl.ods-code-extension": None,
                    "nrl.enable-authorization-lookup": context.application.enable_s3_permissions_lookup,
                    "nrl.permissions": [],
                    "client_rp_details": {
                        "developer.app.name": context.application.app_name,
                        "developer.app.id": context.application.app_id,
                    },
                }
            ),
        )
    )
    if not context.table:
        raise ValueError("No count query table provided")

    items = {row["parameter"]: row["value"] for row in context.table}
    context.response = client.count(items)


@when(
    "the organisation '{ods_code}' requests to search for DocumentReferences with parameters"
)
def search_document_reference_step(context: Context, ods_code: str):
    client = ConsumerClient(
        config=ClientConfig(
            base_url=context.base_url,
            client_cert=context.client_cert,
            connection_metadata=ConnectionMetadata.parse_obj(
                {
                    "nrl.pointer-types": context.application.permissions.get(
                        ods_code, []
                    ),
                    "nrl.ods-code": ods_code,
                    "nrl.ods-code-extension": None,
                    "nrl.enable-authorization-lookup": context.application.enable_s3_permissions_lookup,
                    "nrl.permissions": [],
                    "client_rp_details": {
                        "developer.app.name": context.application.app_name,
                        "developer.app.id": context.application.app_id,
                    },
                }
            ),
        )
    )

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
    "the organisation '{ods_code}' requests to search for DocumentReferences using POST with request body"
)
def search_post_document_reference_step(context: Context, ods_code: str):
    client = ConsumerClient(
        config=ClientConfig(
            base_url=context.base_url,
            client_cert=context.client_cert,
            connection_metadata=ConnectionMetadata.parse_obj(
                {
                    "nrl.pointer-types": context.application.permissions.get(
                        ods_code, []
                    ),
                    "nrl.ods-code": ods_code,
                    "nrl.ods-code-extension": None,
                    "nrl.enable-authorization-lookup": context.application.enable_s3_permissions_lookup,
                    "nrl.permissions": [],
                    "client_rp_details": {
                        "developer.app.name": context.application.app_name,
                        "developer.app.id": context.application.app_id,
                    },
                }
            ),
        )
    )

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


@when(
    "the organisation '{ods_code}' requests to read a DocumentReference with ID '{doc_ref_id}'"
)
def read_document_reference_step(context: Context, ods_code: str, doc_ref_id: str):
    client = ConsumerClient(
        config=ClientConfig(
            base_url=context.base_url,
            client_cert=context.client_cert,
            connection_metadata=ConnectionMetadata.parse_obj(
                {
                    "nrl.pointer-types": context.application.permissions.get(
                        ods_code, []
                    ),
                    "nrl.ods-code": ods_code,
                    "nrl.ods-code-extension": None,
                    "nrl.enable-authorization-lookup": context.application.enable_s3_permissions_lookup,
                    "nrl.permissions": [],
                    "client_rp_details": {
                        "developer.app.name": context.application.app_name,
                        "developer.app.id": context.application.app_id,
                    },
                }
            ),
        )
    )
    context.response = client.read(doc_ref_id)


@then("the response status code is {status_code}")
def assert_response_status_code_step(context: Context, status_code: str):
    assert context.response.status_code == int(
        status_code
    ), f"Expected status code {status_code}, but got {context.response.status_code}\n\nResponse body:\n{context.response.text}"


@then("the response is a {bundle_type} Bundle with a total of {total}")
def assert_response_resource_type_and_count_step(
    context: Context, bundle_type: str, total: str
):
    body = context.response.json()
    assert (
        body["resourceType"] == "Bundle"
    ), f"Expected resourceType 'Bundle', but got {body['resourceType']}"
    assert (
        body["type"] == bundle_type
    ), f'Expected type {bundle_type}, but got {body["type"]}'
    assert body["total"] == int(
        total
    ), f'Expected total {total}, but got {body["total"]}'


@then("the response does not contain the key '{key}'")
def assert_response_no_entries_step(context: Context, key: str):
    assert key not in context.response.json(), f"Key {key} found in response"


@then("the response is a {bundle_type} Bundle with {num_entries} entries")
def assert_response_resource_type_and_entries_step(
    context: Context, bundle_type: str, num_entries: str
):
    body = context.response.json()
    assert body["resourceType"] == "Bundle"
    assert body["type"] == bundle_type
    assert len(body["entry"]) == int(num_entries)


@then("the Bundle contains an DocumentReference entry with values")
def assert_bundle_entry_step(context: Context):
    entries = context.response.json()["entry"]

    if not context.table:
        raise ValueError("No DocumentReference table provided")

    items = {row["property"]: row["value"] for row in context.table}
    if not items.get("id"):
        raise ValueError("No id provided in the table")

    for entry in entries:
        doc_ref = entry["resource"]

        if doc_ref["id"] != items["id"]:
            continue

        if items.get("status"):
            assert (
                doc_ref["status"] == items["status"]
            ), f"Status {doc_ref['status']} does not match expected value: {items['status']}"

        if items.get("type"):
            assert (
                doc_ref["type"]["coding"][0]["code"] == items["type"]
            ), f"Type {doc_ref['type']['coding'][0]['code']} does not match expected value: {items['type']}"

        if items.get("subject"):
            assert (
                doc_ref["subject"]["identifier"]["value"] == items["subject"]
            ), f"Subject {doc_ref['subject']['identifier']['value']} does not match expected value: {items['subject']}"

        if items.get("custodian"):
            assert (
                doc_ref["custodian"]["identifier"]["value"] == items["custodian"]
            ), f"Custodian {doc_ref['custodian']['identifier']['value']} does not match expected value: {items['custodian']}"

        if items.get("contentType"):
            assert (
                doc_ref["content"][0]["attachment"]["contentType"]
                == items["contentType"]
            ), f"ContentType {doc_ref['content'][0]['attachment']['contentType']} does not match expected value: {items['contentType']}"

        if items.get("url"):
            assert (
                doc_ref["content"][0]["attachment"]["url"] == items["url"]
            ), f"URL {doc_ref['content'][0]['attachment']['url']} does not match expected value: {items['url']}"

        return

    raise AssertionError(
        f"DocumentReference with id {items['id']} not found in the response\n\nFull response:\n{json.dumps(context.response.json(), indent=2)}"
    )


@then("the Bundle does not contain a DocumentReference with ID '{doc_ref_id}'")
def assert_bundle_does_not_contain_doc_ref_step(context: Context, doc_ref_id: str):
    entries = context.response.json()["entry"]
    for entry in entries:
        doc_ref = entry["resource"]
        assert (
            doc_ref["id"] != doc_ref_id
        ), f"DocumentReference with id {doc_ref_id} found in the response"


@then("the response is a DocumentReference with JSON value")
def assert_response_document_reference_step(context: Context):
    if not context.text:
        raise ValueError("No DocumentReference JSON provided")

    try:
        content = json.loads(context.text)

    except:
        raise ValueError("Invalid JSON provided")

    assert (
        context.response.json() == content
    ), f"Response does not match expected value:\n\nFull Response:\n{json.dumps(context.response.json(), indent=2)}\n\nExpected Response:\n{json.dumps(content, indent=2)}"


@then("the response is an OperationOutcome with {num_issues} issue")
@then("the response is an OperationOutcome with {num_issues} issues")
def assert_response_operation_outcome_step(context: Context, num_issues: str):
    body = context.response.json()
    assert body["resourceType"] == "OperationOutcome"
    assert len(body["issue"]) == int(num_issues)


@then("the OperationOutcome contains the following issue")
def assert_response_operation_outcome_issue(context: Context):
    if not context.text:
        raise ValueError("No issue JSON provided")

    try:
        content = json.loads(context.text)

    except:
        raise ValueError("Invalid JSON provided")

    for issue in context.response.json()["issue"]:
        if issue == content:
            return

    raise ValueError(
        f"Could not find issue in response:\n\nFull Response:\n{json.dumps(context.response.json(), indent=2)}\n\nExpected Issue:\n{json.dumps(content, indent=2)}"
    )
