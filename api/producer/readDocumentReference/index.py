import sys
import urllib.parse

from pydantic import ValidationError

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata, ReadDocumentReferencePathParams
from nrlf.core.response import Response, SpineErrorResponse
from nrlf.producer.fhir.r4.model import DocumentReference


@request_handler(path=ReadDocumentReferencePathParams)
def handler(
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    path: ReadDocumentReferencePathParams,
) -> Response:
    """
    Entrypoint for the readDocumentReference function
    """
    logger.log(LogReference.PROREAD000)

    parsed_id = urllib.parse.unquote(path.id)

    producer_id = parsed_id.split("-", maxsplit=1)[0]
    if metadata.ods_code_parts != tuple(producer_id.split(".")):
        logger.log(
            LogReference.PROREAD001,
            ods_code_parts=metadata.ods_code_parts,
            producer_id=producer_id,
        )
        return SpineErrorResponse.AUTHOR_CREDENTIALS_ERROR(
            diagnostics="The requested DocumentReference cannot be read because it belongs to another organisation",
        )

    result = repository.get_by_id(parsed_id)
    if result is None:
        logger.log(LogReference.PROREAD002)
        return SpineErrorResponse.NO_RECORD_FOUND(
            diagnostics="The requested DocumentReference could not be found",
        )

    try:
        document_reference = DocumentReference.parse_raw(result.document)
    except ValidationError as exc:
        logger.log(
            LogReference.CONREAD003,
            exc_info=sys.exc_info(),
            stacklevel=5,
            error=str(exc),
        )
        raise OperationOutcomeError(
            status_code="500",
            severity="error",
            code="exception",
            details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
            diagnostics="An error occurred while parsing the document reference",
        ) from exc

    logger.log(LogReference.PROREAD999)
    return Response.from_resource(document_reference)
