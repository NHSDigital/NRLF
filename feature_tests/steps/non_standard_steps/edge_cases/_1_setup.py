import json

from behave.runner import Context

from feature_tests.common.constants import DEFAULT_VERSION, FhirType
from feature_tests.common.decorators import given
from feature_tests.common.models import TestConfig
from nrlf.core.constants import Source
from nrlf.core.model import DocumentPointer
from nrlf.core.transform import make_timestamp
from nrlf.core.validators import json_loads
from nrlf.producer.fhir.r4.model import DocumentReference
from nrlf.producer.fhir.r4.strict_model import (
    DocumentReference as StrictDocumentReference,
)


@given(
    "an invalid Document Pointer exists in the system with the below values for {template_name} template"
)
def given_invalid_document_pointer_exists_with_invalid_document_reference(
    context: Context, template_name: str
):
    test_config: TestConfig = context.test_config
    template = test_config.templates[template_name]
    rendered_template = template.render(
        context.table, fhir_type=FhirType.DocumentReference
    )
    core_model = _invalidate_author_on_document_reference_object(rendered_template)

    table_name = test_config.environment_prefix + core_model.kebab()
    test_config.dynamodb_client.put_item(TableName=table_name, Item=core_model.dict())


@given(
    "an invalid Document Pointer exists in the system with an invalid NHS Number and the below values for {template_name} template"
)
def given_invalid_document_pointer_exists_with_invalid_nhs_number(
    context: Context, template_name: str
):
    test_config: TestConfig = context.test_config
    template = test_config.templates[template_name]
    rendered_template = template.render(
        context.table, fhir_type=FhirType.DocumentReference
    )
    core_model = _invalidate_nhs_number_on_document_pointer_object(rendered_template)

    table_name = test_config.environment_prefix + "document-pointer"
    test_config.dynamodb_client.put_item(TableName=table_name, Item=core_model)


def _invalidate_author_on_document_reference_object(rendered_template):
    modify_template = json_loads(rendered_template)
    author = modify_template["author"]
    del modify_template["author"]

    core_model = _create_invalid_document_pointer_from_fhir_json(
        fhir_json=json_loads(json.dumps(modify_template)),
        api_version=int(DEFAULT_VERSION),
    )

    document = json_loads(core_model.document.__root__)
    document["author"] = author
    core_model.document = {"S": json.dumps(document)}
    return core_model


def _invalidate_nhs_number_on_document_pointer_object(rendered_template):
    modify_template = json_loads(rendered_template)
    core_model = _create_invalid_document_pointer_with_invalid_nhs_number(
        fhir_json=json_loads(json.dumps(modify_template)),
        api_version=int(DEFAULT_VERSION),
    )
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
        custodian=fhir_model.custodian.identifier.value,
        type=fhir_model.type,
        version=api_version,
        document=json.dumps(fhir_json),
        source=source.value,
        created_on=kwargs.pop("created_on", make_timestamp()),
        **kwargs,
    )
    return core_model


def _create_invalid_document_pointer_with_invalid_nhs_number(
    fhir_json: dict,
    api_version: int,
    source: Source = Source.NRLF,
    **kwargs,
) -> DocumentPointer:
    fhir_model = _create_fhir_model_from_fhir_json(fhir_json=fhir_json)
    core_model = DocumentPointer(
        id=fhir_model.id,
        nhs_number="9278693472",
        custodian=fhir_model.custodian.identifier.value,
        type=fhir_model.type,
        version=api_version,
        document=json.dumps(fhir_json),
        source=source.value,
        created_on=kwargs.pop("created_on", make_timestamp()),
        **kwargs,
    )
    core_model_dict = core_model.dict()
    core_model_dict["nhs_number"] = {"S": "92786934721"}
    return core_model_dict


def _create_fhir_model_from_fhir_json(fhir_json: dict) -> StrictDocumentReference:
    DocumentReference(**fhir_json)
    fhir_strict_model = StrictDocumentReference(**fhir_json)
    return fhir_strict_model
