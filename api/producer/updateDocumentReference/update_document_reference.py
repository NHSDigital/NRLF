import urllib.parse

from pydantic import ValidationError

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.dynamodb.model import DocumentPointer
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata, UpdateDocumentReferencePathParams
from nrlf.core.response import NRLResponse, Response, SpineErrorResponse
from nrlf.core.utils import create_fhir_instant
from nrlf.core.validators import DocumentReferenceValidator
from nrlf.producer.fhir.r4.model import DocumentReference, Meta


def _set_update_time_fields(
    update_time: str, document_reference: DocumentReference
) -> DocumentReference:
    """
    Set the lastUpdated timestamp on the provided DocumentReference
    """
    if not document_reference.meta:
        document_reference.meta = Meta()
    document_reference.meta.lastUpdated = update_time

    return document_reference


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

    update_time = create_fhir_instant()
    document_reference = _set_update_time_fields(
        update_time, document_reference=result.resource
    )

    core_model = DocumentPointer.from_document_reference(document_reference)

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
            diagnostics="An error occurred whilst parsing the existing document reference",
        )

    preserved_fields = ["date"]
    for field in preserved_fields:
        provided_field = getattr(result.resource, field, None)
        existing_field = getattr(existing_resource, field, None)
        if provided_field and provided_field != existing_field:
            logger.log(
                LogReference.PROUPDATE007,
                field=field,
                provided=provided_field,
            )
        setattr(document_reference, field, existing_field)

    immutable_fields = [
        "masterIdentifier",
        "id",
        "identifier",
        "status",
        "type",
        "subject",
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

    document_pointer_update = DocumentPointer.from_document_reference(
        document_reference
    )
    document_pointer_update.created_on = existing_model.created_on
    document_pointer_update.updated_on = update_time

    repository.update(document_pointer_update)

    logger.log(LogReference.PROUPDATE999)
    return NRLResponse.RESOURCE_UPDATED()
