import urllib.parse

from nrlf.core.decorators import (
    APIGatewayProxyEvent,
    DocumentPointerRepository,
    request_handler,
)
from nrlf.core.model import ConnectionMetadata
from nrlf.core.response import Response, SpineErrorConcept
from nrlf.producer.fhir.r4.model import DocumentReference, OperationOutcomeIssue


@request_handler()
def handler(
    event: APIGatewayProxyEvent,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Entrypoint for the readDocumentReference function
    """
    subject = (event.path_parameters or {}).get("id", "unknown")
    parsed_id = urllib.parse.unquote(subject)

    producer_id = parsed_id.split("-", maxsplit=1)[0]
    if metadata.ods_code_parts != tuple(producer_id.split(".")):
        return Response.from_issues(
            statusCode="403",
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="forbidden",
                    details=SpineErrorConcept.from_code("AUTHOR_CREDENTIALS_ERROR"),
                    diagnostics="The requested document pointer cannot be read because it belongs to another organisation",
                )
            ],
        )

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
