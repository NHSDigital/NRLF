from nrlf.core.constants import Categories, PointerTypes
from nrlf.producer.fhir.r4.model import (
    Attachment,
    CodeableConcept,
    Coding,
    DocumentReference,
    DocumentReferenceContent,
    DocumentReferenceRelatesTo,
    Identifier,
    Reference,
)
from tests.utilities.api_clients import ProducerTestClient


def build_document_reference(
    nhs_number: str,
    custodian: str = "SMOKETEST",
    status: str = "current",
    category: str = Categories.CARE_PLAN.coding_value(),
    type: str = PointerTypes.MENTAL_HEALTH_PLAN.coding_value(),
    author: str = "SMOKETEST",
    content_type: str = "application/json",
    content_url: str = "https://testing.record-locator.national.nhs.uk/_smoke_test_pointer_content",
    replaces_id: str | None = None,
) -> DocumentReference:
    docref = DocumentReference(
        resourceType="DocumentReference",
        status=status,
        content=[
            DocumentReferenceContent(
                attachment=Attachment(
                    contentType=content_type,
                    url=content_url,
                )
            )
        ],
        type=CodeableConcept(
            coding=[Coding(system="http://snomed.info/sct", code=type)]
        ),
        subject=Reference(
            identifier=Identifier(
                system="https://fhir.nhs.uk/Id/nhs-number", value=nhs_number
            )
        ),
        custodian=Reference(
            identifier=Identifier(
                system="https://fhir.nhs.uk/Id/ods-organization-code", value=custodian
            )
        ),
        author=[
            Reference(
                identifier=Identifier(
                    system="https://fhir.nhs.uk/Id/ods-organization-code", value=author
                )
            )
        ],
        category=[
            CodeableConcept(
                coding=[
                    Coding(
                        system="http://snomed.info/sct",
                        code=category,
                        display=(
                            "Care plan" if category == "734163000" else "Observations"
                        ),
                    )
                ]
            )
        ],
    )

    if replaces_id:
        docref.relatesTo = [
            DocumentReferenceRelatesTo(
                code="replaces",
                target=Reference(
                    type="DocumentReference",
                    identifier=Identifier(
                        system="https://fhir.nhs.uk/Id/",
                        value=replaces_id,
                    ),
                ),
            )
        ]

    return docref


def upsert_test_pointer(
    id: str, docref: DocumentReference, producer_client: ProducerTestClient
) -> DocumentReference:
    docref.id = id

    create_response = producer_client.upsert(docref.model_dump())

    if not create_response.ok:
        raise ValueError(f"Failed to create test pointer: {create_response.text}")

    return docref
