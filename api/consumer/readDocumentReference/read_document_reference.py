import sys
import urllib.parse

from pydantic import ValidationError

from nrlf.consumer.fhir.r4.model import DocumentReference
from nrlf.core.decorators import request_handler
from nrlf.core.dynamodb.repository import DocumentPointerRepository
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata, ReadDocumentReferencePathParams
from nrlf.core.response import Response, SpineErrorConcept, SpineErrorResponse


@request_handler(path=ReadDocumentReferencePathParams)
def handler(
    repository: DocumentPointerRepository,
    metadata: ConnectionMetadata,
    path: ReadDocumentReferencePathParams,
) -> Response:
    """
    Reads a document reference based on the provided parameters.

    Args:
        repository (DocumentPointerRepository): The repository used to retrieve the document reference.
        metadata (ConnectionMetadata): The metadata containing connection information.
        path (ReadDocumentReferencePathParams): The path parameters for the document reference.

    Returns:
        Response: The response containing the document reference.

    Raises:
        OperationOutcomeError: If an error occurs while parsing the document reference.
        SpineErrorResponse: If the requested document reference is not found or access is denied.
    """

    logger.log(LogReference.CONREAD000)

    parsed_id = urllib.parse.unquote(path.id)
    result = repository.get_by_id(parsed_id)

    if result is None:
        logger.log(LogReference.CONREAD001)
        return SpineErrorResponse.NO_RECORD_FOUND(
            diagnostics="The requested DocumentReference could not be found"
        )

    if result.type not in metadata.pointer_types:
        logger.log(
            LogReference.CONREAD002,
            ods_code=metadata.ods_code,
            type=result.type,
            pointer_types=metadata.pointer_types,
        )
        return SpineErrorResponse.ACCESS_DENIED(
            diagnostics="The requested DocumentReference is not of a type that this organisation is allowed to access"
        )

    try:
        document_reference = DocumentReference.parse_raw(result.document)
    except ValidationError as exc:
        logger.log(
            LogReference.CONREAD003,
            exc_info=sys.exc_info(),
            error=str(exc),
        )
        raise OperationOutcomeError(
            status_code="500",
            severity="error",
            code="exception",
            details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
            diagnostics="An error occurred while parsing the document reference",
        ) from exc

    response = Response.from_resource(document_reference)
    logger.log(LogReference.CONREAD999)

    return response
