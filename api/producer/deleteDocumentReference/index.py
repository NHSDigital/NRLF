import urllib.parse

from nrlf.core.codes import NRLResponseConcept, SpineErrorConcept
from nrlf.core.decorators import (
    APIGatewayProxyEvent,
    DocumentPointerRepository,
    request_handler,
)
from nrlf.core.model import ConnectionMetadata
from nrlf.core.response import Response
from nrlf.producer.fhir.r4.model import OperationOutcomeIssue


@request_handler()
def handler(
    event: APIGatewayProxyEvent,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Entrypoint for the deleteDocumentReference function
    """
    pointer_id = urllib.parse.unquote(
        (event.path_parameters or {}).get("id", "unknown")
    )
    producer_id, _ = pointer_id.split("-", 1)

    if metadata.ods_code_parts != tuple(producer_id.split(".")):
        return Response.from_issues(
            statusCode="403",
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="forbidden",
                    details=SpineErrorConcept.from_code("AUTHOR_CREDENTIALS_ERROR"),
                    diagnostics="The requested document pointer cannot be deleted because it belongs to another organisation",
                )
            ],
        )

    if not (core_model := repository.get_by_id(pointer_id)):
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

    repository.delete(core_model)

    return Response.from_issues(
        statusCode="200",
        issues=[
            OperationOutcomeIssue(
                severity="information",
                code="informational",
                details=NRLResponseConcept.from_code("RESOURCE_DELETED"),
                diagnostics="The requested document pointer has been deleted",
            )
        ],
    )
