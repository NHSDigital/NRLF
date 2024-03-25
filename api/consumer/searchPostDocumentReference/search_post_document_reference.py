from pydantic import ValidationError

from nrlf.consumer.fhir.r4.model import Bundle, DocumentReference
from nrlf.core.codes import SpineErrorConcept
from nrlf.core.decorators import request_handler
from nrlf.core.dynamodb.repository import DocumentPointerRepository
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata, ConsumerRequestParams
from nrlf.core.response import Response, SpineErrorResponse
from nrlf.core.validators import validate_type_system


@request_handler(body=ConsumerRequestParams)
def search_post_document_reference(
    body: ConsumerRequestParams,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Search for document references based on the provided parameters.

    Args:
        body (ConsumerRequestParams): The request parameters for the search.
        metadata (ConnectionMetadata): The metadata containing pointer types.
        repository (DocumentPointerRepository): The repository for document pointers.

    Returns:
        Response: The response containing the search results.

    Raises:
        SpineErrorResponse.INVALID_NHS_NUMBER: If a valid NHS number is not provided.
        SpineErrorResponse.INVALID_CODE_SYSTEM: If the provided type system is invalid.
        OperationOutcomeError: If an error occurs while parsing the document reference.
    """

    logger.log(LogReference.CONPOSTSEARCH000)

    if not body.nhs_number:
        logger.log(
            LogReference.CONPOSTSEARCH001, subject_identifier=body.subject_identifier
        )
        return SpineErrorResponse.INVALID_NHS_NUMBER(
            diagnostics="A valid NHS number is required to search for document references",
            expression="subject:identifier",
        )

    if not validate_type_system(body.type, metadata.pointer_types):
        logger.log(
            LogReference.CONPOSTSEARCH002,
            type=body.type,
            pointer_types=metadata.pointer_types,
        )
        return SpineErrorResponse.INVALID_CODE_SYSTEM(
            diagnostics="Invalid type (The provided type system does not match the allowed types for this organisation)",
            expression="type",
        )

    custodian_id = (
        body.custodian_identifier.__root__.split("|", maxsplit=1)[0]
        if body.custodian_identifier
        else None
    )

    bundle = {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}
    pointer_types = [body.type.__root__] if body.type else metadata.pointer_types

    logger.log(
        LogReference.CONPOSTSEARCH003,
        nhs_number=body.nhs_number,
        custodian_id=custodian_id,
        pointer_types=pointer_types,
    )

    for result in repository.search(
        nhs_number=body.nhs_number, custodian=custodian_id, pointer_types=pointer_types
    ):
        try:
            document_reference = DocumentReference.parse_raw(result.document)
            bundle["total"] += 1
            bundle["entry"].append(
                {"resource": document_reference.dict(exclude_none=True)}
            )
            logger.log(
                LogReference.CONPOSTSEARCH004,
                id=document_reference.id,
                count=bundle["total"],
            )

        except ValidationError as exc:
            logger.log(
                LogReference.CONPOSTSEARCH005, error=str(exc), document=result.document
            )
            raise OperationOutcomeError(
                status_code="500",
                severity="error",
                code="exception",
                details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
                diagnostics="An error occurred whilst parsing the document reference search results",
            ) from exc

    response = Response.from_resource(Bundle.parse_obj(bundle))
    logger.log(LogReference.CONPOSTSEARCH999)

    return response
