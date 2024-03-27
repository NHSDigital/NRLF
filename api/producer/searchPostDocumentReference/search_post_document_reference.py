from pydantic import ValidationError

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata, ProducerRequestParams
from nrlf.core.response import Response, SpineErrorResponse
from nrlf.core.validators import validate_type_system
from nrlf.producer.fhir.r4.model import Bundle, DocumentReference


@request_handler(body=ProducerRequestParams)
def handler(
    body: ProducerRequestParams,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Search for document references based on the provided parameters.

    Args:
        body (ProducerRequestParams): The request parameters for the search.
        metadata (ConnectionMetadata): The connection metadata.
        repository (DocumentPointerRepository): The repository for document pointers.

    Returns:
        Response: The response containing the search results.

    Raises:
        OperationOutcomeError: If an error occurs while parsing the document reference.
    """

    logger.log(LogReference.PROPOSTSEARCH000)

    if not body.nhs_number:
        logger.log(
            LogReference.PROPOSTSEARCH001, subject_identifier=body.subject_identifier
        )
        return SpineErrorResponse.INVALID_NHS_NUMBER(
            diagnostics="A valid NHS number is required to search for document references",
            expression="subject:identifier",
        )

    if not validate_type_system(body.type, metadata.pointer_types):
        logger.log(
            LogReference.PROPOSTSEARCH002,
            type=body.type,
            pointer_types=metadata.pointer_types,
        )
        return SpineErrorResponse.INVALID_CODE_SYSTEM(
            diagnostics="The provided type system does not match the allowed types for this organisation",
            expression="type",
        )

    pointer_types = [body.type.__root__] if body.type else metadata.pointer_types
    bundle = {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}

    logger.log(
        LogReference.PROPOSTSEARCH003,
        custodian=metadata.ods_code,
        custodian_suffix=metadata.ods_code_extension,
        nhs_number=body.nhs_number,
        pointer_types=pointer_types,
    )

    for result in repository.search_by_custodian(
        custodian=metadata.ods_code,
        custodian_suffix=metadata.ods_code_extension,
        nhs_number=body.nhs_number,
        pointer_types=pointer_types,
    ):
        try:
            document_reference = DocumentReference.parse_raw(result.document)
            bundle["total"] += 1
            bundle["entry"].append(
                {"resource": document_reference.dict(exclude_none=True)}
            )
            logger.log(
                LogReference.PROPOSTSEARCH004,
                id=document_reference.id,
                count=bundle["total"],
            )

        except ValidationError as exc:
            logger.log(
                LogReference.PROPOSTSEARCH005, error=str(exc), document=result.document
            )
            raise OperationOutcomeError(
                status_code="500",
                severity="error",
                code="exception",
                details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
                diagnostics="An error occurred whilst parsing the document reference search results",
            )

    logger.log(LogReference.PROPOSTSEARCH999)
    return Response.from_resource(Bundle.parse_obj(bundle))
