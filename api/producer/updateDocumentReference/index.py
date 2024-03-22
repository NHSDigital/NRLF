import urllib.parse

from pydantic import ValidationError

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.dynamodb.model import DocumentPointer
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata, UpdateDocumentReferencePathParams
from nrlf.core.response import NRLResponse, Response, SpineErrorResponse
from nrlf.core.validators import DocumentReferenceValidator
from nrlf.producer.fhir.r4.model import DocumentReference


@request_handler(body=DocumentReference, path=UpdateDocumentReferencePathParams)
def handler(
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    body: DocumentReference,
    path: UpdateDocumentReferencePathParams,
) -> Response:
    """
    Entrypoint for the updateDocumentReference function
    """
    logger.log(LogReference.PROUPDATE000)

    if body.id != path.id:
        logger.log(LogReference.PROUPDATE001, body_id=body.id, path_id=path.id)
        return SpineErrorResponse.BAD_REQUEST(
            diagnostics="The document id in the path does not match the document id in the body"
        )

    logger.log(LogReference.PROUPDATE002, body=body)

    validator = DocumentReferenceValidator()
    result = validator.validate(body)

    if not result.is_valid:
        logger.log(LogReference.PROUPDATE003)
        return Response.from_issues(statusCode="400", issues=result.issues)

    core_model = DocumentPointer.from_document_reference(result.resource)

    if metadata.ods_code_parts != tuple(core_model.producer_id.split("|")):
        logger.log(
            LogReference.PROUPDATE004,
            metadata_ods_code_parts=metadata.ods_code_parts,
            producer_id=core_model.producer_id,
        )
        return SpineErrorResponse.AUTHOR_CREDENTIALS_ERROR(
            diagnostics="The id of the provided DocumentReference does not include the expected ODS code for this organisation"
        )

    pointer_id = urllib.parse.quote_plus(path.id)
    if not (existing_model := repository.get_by_id(pointer_id)):
        logger.log(LogReference.PROUPDATE005, pointer_id=pointer_id)
        return SpineErrorResponse.NO_RECORD_FOUND(
            diagnostics="The requested DocumentReference could not be found"
        )

    try:
        existing_resource = DocumentReference.parse_raw(existing_model.document)
    except ValidationError as exc:
        logger.log(LogReference.PROUPDATE002, error=exc)
        raise OperationOutcomeError(
            status_code="500",
            severity="error",
            code="exception",
            details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
            diagnostics="An error occurred while parsing the existing document reference",
        )

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
            logger.log(LogReference.PROUPDATE006, field=field)
            return SpineErrorResponse.BAD_REQUEST(
                diagnostics=f"The field '{field}' is immutable and cannot be updated",
                expression=field,
            )

    repository.update(core_model)

    logger.log(LogReference.PROUPDATE999)
    return NRLResponse.RESOURCE_UPDATED()
