from nrlf.producer.fhir.r4.model import (
    Attachment,
    CodeableConcept,
    Coding,
    DocumentReference,
    DocumentReferenceContent,
    Identifier,
    Reference,
)


def create_test_document_reference(items: dict) -> DocumentReference:
    base_doc_ref = DocumentReference(
        resourceType="DocumentReference",
        status=items.get("status", "current"),
        content=[
            DocumentReferenceContent(
                attachment=Attachment(
                    contentType=items.get("contentType", "application/json"),
                    url=items["url"],
                )
            )
        ],
    )

    if items.get("id"):
        base_doc_ref.id = items["id"]

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

    if items.get("author"):
        base_doc_ref.author = [
            Reference(
                identifier=Identifier(
                    system="https://fhir.nhs.uk/Id/ods-organization-code",
                    value=items["author"],
                )
            )
        ]

    if items.get("category"):
        base_doc_ref.category = [
            CodeableConcept(
                coding=[Coding(system="http://snomed.info/sct", code=items["category"])]
            )
        ]

    return base_doc_ref
