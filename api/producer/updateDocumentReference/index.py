from nrlf.core.codes import NRLResponseConcept
from nrlf.core.decorators import (
    APIGatewayProxyEvent,
    DocumentPointerRepository,
    request_handler,
)
from nrlf.core.dynamodb.model import DocumentPointer
from nrlf.core.model import ConnectionMetadata
from nrlf.core.response import Response, SpineErrorConcept
from nrlf.core.validators import DocumentReferenceValidator
from nrlf.producer.fhir.r4.model import DocumentReference, OperationOutcomeIssue


@request_handler(body=DocumentReference)
def handler(
    event: APIGatewayProxyEvent,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    body: DocumentReference,
) -> Response:
    """
    Entrypoint for the updateDocumentReference function
    """
    if not (pointer_id := (event.path_parameters or {}).get("id")):
        return Response.from_issues(
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("INVALID_IDENTIFIER_VALUE"),
                    diagnostics="Invalid document reference ID provided in the path parameters",
                )
            ],
            statusCode="400",
        )

    if body.id != pointer_id:
        return Response.from_issues(
            statusCode="400",
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("BAD_REQUEST"),
                    diagnostics="The document id in the path does not match the document id in the body",
                )
            ],
        )

    validator = DocumentReferenceValidator()

    result = validator.validate(body)

    if not result.is_valid:
        return Response.from_issues(statusCode="400", issues=result.issues)

    core_model = DocumentPointer.from_document_reference(result.resource)

    if metadata.ods_code_parts != tuple(core_model.producer_id.split("|")):
        return Response.from_issues(
            statusCode="401",
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("AUTHOR_CREDENTIALS_ERROR"),
                    diagnostics="The id of the provided document pointer does not include the expected organisation code for this app",
                )
            ],
        )

    if not (existing_model := repository.get_by_id(pointer_id)):
        return Response.from_issues(
            statusCode="404",
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="not-found",
                    details=SpineErrorConcept.from_code("NO_RECORD_FOUND"),
                    diagnostics="The requested document pointer could not be found",
                )
            ],
        )

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
            return Response.from_issues(
                statusCode="400",
                issues=[
                    OperationOutcomeIssue(
                        severity="error",
                        code="invalid",
                        details=SpineErrorConcept.from_code("BAD_REQUEST"),
                        diagnostics=f"The field '{field}' is immutable and cannot be updated",
                    )
                ],
            )

    repository.update(core_model)

    return Response.from_issues(
        statusCode="200",
        issues=[
            OperationOutcomeIssue(
                severity="information",
                code="informational",
                details=NRLResponseConcept.from_code("RESOURCE_UPDATED"),
                diagnostics="The document reference has been updated",
            )
        ],
    )
