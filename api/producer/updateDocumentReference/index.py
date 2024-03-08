from nrlf.core_nonpipeline.decorators import (
    APIGatewayProxyEvent,
    ConnectionMetadata,
    DocumentPointerRepository,
    request_handler,
)
from nrlf.core_nonpipeline.dynamodb.model import DocumentPointer
from nrlf.core_nonpipeline.errors import OperationOutcomeResponse
from nrlf.core_nonpipeline.transform import DocumentReferenceValidator, ParseError
from nrlf.producer.fhir.r4.model import (
    CodeableConcept,
    Coding,
    DocumentReference,
    OperationOutcome,
    OperationOutcomeIssue,
)


@request_handler()
def handler(
    event: APIGatewayProxyEvent,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    **_,
):
    """
    Entrypoint for the updateDocumentReference function
    """
    subject = (event.path_parameters or {}).get("id", "unknown")

    body = event.json_body
    if not body:
        return {"statusCode": "400", "body": "Bad Request"}

    if "id" in body and body["id"] != subject:
        # InconsistentUpdateId
        raise Exception(
            "Document id in path does not match the document id in the body"
        )

    validator = DocumentReferenceValidator()

    try:
        result = validator.validate(body)

    except ParseError as error:
        raise OperationOutcomeResponse(issues=error.issues)

    if not result.is_valid:
        raise OperationOutcomeResponse(issues=result.issues)

    core_model = DocumentPointer.from_document_reference(result.resource)

    # TODO: Data contracts
    if metadata.ods_code_parts != tuple(core_model.producer_id.split("|")):
        # TODO: ProducerValidationError
        raise Exception(
            "The id of the provided document pointer does not include the expected organisation code for this app"
        )

    if not (existing_model := repository.get_by_id(subject)):
        return {"statusCode": "404", "body": "Not Found"}

    existing_resource = DocumentReference.parse_raw(existing_model.document)

    immutable_fields = [
        "masterIdentifier",
        "id",
        "identifier",
        "status",
        "type",
        "subject",
        "date",
        "custodian",
        "relatesTo",
        "author",
    ]

    for field in immutable_fields:
        if getattr(result.resource, field) != getattr(existing_resource, field):
            raise Exception(f"The field {field} is immutable and cannot be updated")

    repository.update(core_model)

    operation_outcome = OperationOutcome(
        resourceType="OperationOutcome",
        issue=[
            OperationOutcomeIssue(
                severity="information",
                code="informational",
                details=CodeableConcept(
                    coding=[
                        Coding(
                            system="https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                            code="RESOURCE_UPDATED",
                            display="Resource updated",
                        )
                    ]
                ),
            )
        ],
    )

    return {
        "statusCode": "200",
        "body": operation_outcome.json(exclude_none=True, indent=2),
    }
