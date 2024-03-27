import urllib.parse

from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata, DeleteDocumentReferencePathParams
from nrlf.core.response import NRLResponse, Response, SpineErrorResponse


@request_handler(path=DeleteDocumentReferencePathParams)
def handler(
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    path: DeleteDocumentReferencePathParams,
) -> Response:
    """
    Deletes a document reference.

    Args:
        metadata (ConnectionMetadata): The connection metadata.
        repository (DocumentPointerRepository): The document pointer repository.
        path (DeleteDocumentReferencePathParams): The path parameters.

    Returns:
        Response: The response indicating the result of the deletion.
    """
    logger.log(LogReference.PRODELETE000)

    pointer_id = urllib.parse.unquote(path.id)
    producer_id, _ = pointer_id.split("-", 1)

    if metadata.ods_code_parts != tuple(producer_id.split(".")):
        logger.log(
            LogReference.PRODELETE001,
            ods_code_parts=metadata.ods_code_parts,
            producer_id=producer_id,
        )
        return SpineErrorResponse.AUTHOR_CREDENTIALS_ERROR(
            diagnostics="The requested DocumentReference cannot be deleted because it belongs to another organisation",
        )

    if not (core_model := repository.get_by_id(pointer_id)):
        logger.log(LogReference.PRODELETE002, pointer_id=pointer_id)
        return SpineErrorResponse.NO_RECORD_FOUND(
            diagnostics="The requested DocumentReference could not be found",
        )

    repository.delete(core_model)

    logger.log(LogReference.PRODELETE999)
    return NRLResponse.RESOURCE_DELETED()
