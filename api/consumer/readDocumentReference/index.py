import urllib.parse

from nrlf.consumer.fhir.r4.model import DocumentReference, OperationOutcomeIssue
from nrlf.core.decorators import APIGatewayProxyEvent, request_handler
from nrlf.core.dynamodb.repository import DocumentPointerRepository
from nrlf.core.response import Response, SpineErrorConcept


@request_handler()
def handler(
    event: APIGatewayProxyEvent, repository: DocumentPointerRepository
) -> Response:
    """
    Entrypoint for the readDocumentReference function
    """
    if not (subject := (event.path_parameters or {}).get("id")):
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

    parsed_id = urllib.parse.unquote(subject)
    result = repository.get_by_id(parsed_id)

    if result is None:
        return Response.from_issues(
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="not-found",
                    details=SpineErrorConcept.from_code("NO_RECORD_FOUND"),
                    diagnostics="The requested document pointer could not be found",
                )
            ],
            statusCode="404",
        )

    document_reference = DocumentReference.parse_raw(result.document)
    return Response.from_resource(document_reference)
