from behave.runner import Context
from nrlf.core.dynamodb_types import convert_dynamo_value_to_raw_value
from nrlf.core.model import DocumentPointer, convert_document_pointer_id_to_pk
from nrlf.core.validators import validate_timestamp

from feature_tests.common.decorators import then
from feature_tests.common.models import TestConfig
from feature_tests.common.repository import FeatureTestRepository


@then('Document Pointer "{id}" exists')
def assert_document_pointer_exists(context: Context, id: str):
    test_config: TestConfig = context.test_config
    repository: FeatureTestRepository = test_config.repositories[DocumentPointer]
    pk = convert_document_pointer_id_to_pk(id)
    item, exists, message = repository.exists(pk)
    assert exists, message
    (sent_document,) = test_config.request.sent_documents
    for row in context.table:
        dynamo_value = convert_dynamo_value_to_raw_value(getattr(item, row["property"]))
        property_type = type(dynamo_value)
        if row["value"] == "<document>":
            assert dynamo_value == sent_document, dynamo_value
        elif row["value"] == "NULL":
            assert dynamo_value is None
        elif row["value"] == "<timestamp>":
            validate_timestamp(dynamo_value)
        else:
            assert dynamo_value == property_type(
                row["value"]
            ), f'expected {row["value"]} got {dynamo_value}'


@then('Document Pointer "{id}" still exists')
def assert_document_pointer_exists(context: Context, id: str):
    test_config: TestConfig = context.test_config
    repository: FeatureTestRepository = test_config.repositories[DocumentPointer]
    pk = convert_document_pointer_id_to_pk(id)
    item, exists, message = repository.exists(pk)
    assert exists, message


@then('Document Pointer "{id}" does not exist')
def assert_document_pointer_does_not_exist(context: Context, id: str):
    test_config: TestConfig = context.test_config
    repository: FeatureTestRepository = test_config.repositories[DocumentPointer]
    pk = convert_document_pointer_id_to_pk(id)
    _, exists, message = repository.exists(pk)
    assert not exists, message
