import json

from behave import *  # noqa
from behave.runner import Context
from pydantic.v1 import BaseModel

from nrlf.core.boto import get_s3_client
from nrlf.core.dynamodb.model import DocumentPointer
from tests.features.utils.data import create_test_document_reference


class Application(BaseModel):
    app_id: str = "UNSET"
    app_name: str = "UNSET"
    enable_s3_permissions_lookup: bool = False
    pointer_types: dict[str, list[str]] = {}

    def add_pointer_types(self, ods_code: str, pointer_types: list[str]):
        self.pointer_types[ods_code] = pointer_types


@given("the application '{app_name}' (ID '{app_id}') is registered to access the API")
def register_application_step(context: Context, app_name: str, app_id: str):
    context.application = Application(app_id=app_id, app_name=app_name)


@given("the organisation '{ods_code}' is authorised to access pointer types")
def register_org_permissions_step(context: Context, ods_code: str):
    if not context.table:
        raise ValueError("No permissions table provided")

    pointer_types = [f"{system}|{value}" for system, value in context.table]
    context.application.add_pointer_types(ods_code, pointer_types)


@given("the application is configured to lookup permissions from S3")
def enable_s3_permissions_lookup_step(context: Context):
    context.application.enable_s3_permissions_lookup = True


@given("the organisation '{ods_code}' is authorised in S3 to access pointer types")
def register_org_permissions_s3_step(context: Context, ods_code: str):
    if not context.table:
        raise ValueError("No permissions table provided")

    pointer_types = [f"{system}|{value}" for system, value in context.table]
    bucket = f"nhsd-nrlf--{context.env}--authorization-store"
    key = f"{context.application.app_id}/{ods_code}.json"

    s3_client = get_s3_client()
    s3_client.put_object(Bucket=bucket, Key=key, Body=json.dumps(pointer_types))
    context.add_cleanup(lambda: s3_client.delete_object(Bucket=bucket, Key=key))


@given("a DocumentReference resource exists with values")
def create_document_reference_step(context: Context):
    if not context.table:
        raise ValueError("No DocumentReference table provided")

    items = {row["property"]: row["value"] for row in context.table}
    base_doc_ref = create_test_document_reference(items)
    doc_pointer = DocumentPointer.from_document_reference(base_doc_ref)

    context.repository.create(doc_pointer)
    context.add_cleanup(lambda: context.repository.delete(doc_pointer))
