from nrlf.core.codes import NRLResponseConcept, SpineErrorConcept
from nrlf.core.decorators import APIGatewayProxyEvent, request_handler
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.core.model import ConnectionMetadata
from nrlf.core.response import Response
from nrlf.core.transform import DocumentReferenceValidator, ParseError
from nrlf.producer.fhir.r4.model import OperationOutcomeIssue


@request_handler()
def handler(
    event: APIGatewayProxyEvent,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Entrypoint for the createDocumentReference function
    """
    if not event.body:
        return Response.from_issues(
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="bad-request",
                    details=SpineErrorConcept.from_code("BAD_REQUEST"),
                    diagnostics="The request body is empty",
                )
            ],
            statusCode="400",
        )

    body = event.json_body
    validator = DocumentReferenceValidator()

    try:
        result = validator.validate(body)

    except ParseError as error:
        return Response.from_issues(issues=error.issues, statusCode="400")

    if not result.is_valid:
        return Response.from_issues(issues=result.issues, statusCode="400")

    # TODO: Do data contract validation here

    core_model = DocumentPointer.from_document_reference(result.resource)

    if metadata.ods_code_parts != tuple(core_model.producer_id.split("|")):
        # TODO: ProducerValidationError
        raise Exception(
            "The id of the provided document pointer does not include the expected organisation code for this app"
        )

    custodian_parts = tuple(
        filter(None, (core_model.custodian, core_model.custodian_suffix))
    )
    if metadata.ods_code_parts != custodian_parts:
        raise Exception(
            "The custodian of the provided document pointer does not match the expected organisation code for this app"
        )

    if core_model.type not in metadata.pointer_types:
        raise Exception(
            "The type of the provided document pointer is in the list of allowed types for this app"
        )

    if result.resource.relatesTo:
        superseded_ids = []

        for relates_to in result.resource.relatesTo:
            if not (identifier := getattr(relates_to.target, "identifier", None)):
                raise Exception("No identifier provider for supersede target")

            producer_id = identifier.split("-", 1)[0]
            if metadata.ods_code_parts != tuple(producer_id.split("|")):
                raise Exception(
                    "At least one document pointer cannot be deleted because it belongs to another organisation"
                )

            if not (pointer := repository.get_by_id(identifier)):
                # Original - SupersedeValidationError
                raise Exception(
                    "Validation failure - relatesTo target document does not exist"
                )

            if pointer.nhs_number != core_model.nhs_number:
                raise Exception(
                    "Validation failure - relatesTo target document nhs number does not match the request"
                )

            if pointer.type != core_model.type:
                raise Exception(
                    "Validation failure - relatesTo target document type does not match the request"
                )

            superseded_ids.append(identifier)

        saved_model = repository.supersede(core_model, superseded_ids)

        return Response.from_issues(
            issues=[
                OperationOutcomeIssue(
                    severity="information",
                    code="informational",
                    details=NRLResponseConcept.from_code("RESOURCE_SUPERSEDED"),
                    diagnostics="The document has been superseded by a new version",
                )
            ],
            statusCode="201",
        )

    saved_model = repository.create(core_model)

    return Response.from_issues(
        issues=[
            OperationOutcomeIssue(
                severity="information",
                code="informational",
                details=NRLResponseConcept.from_code("RESOURCE_CREATED"),
                diagnostics="The document has been created",
            )
        ],
        statusCode="201",
    )
