from nrlf.core.decorators import request_handler
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata
from nrlf.core.response import NRLResponse, Response, SpineErrorResponse
from nrlf.core.validators import DocumentReferenceValidator
from nrlf.producer.fhir.r4.model import DocumentReference


@request_handler(body=DocumentReference)
def handler(
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    body: DocumentReference,
) -> Response:
    """
    Entrypoint for the createDocumentReference function
    """
    logger.log(LogReference.PROCREATE000)

    logger.log(LogReference.PROCREATE001, resource=body)
    validator = DocumentReferenceValidator()
    result = validator.validate(body)

    if not result.is_valid:
        logger.log(LogReference.PROCREATE002)
        return Response.from_issues(issues=result.issues, statusCode="400")

    core_model = DocumentPointer.from_document_reference(result.resource)

    if metadata.ods_code_parts != tuple(core_model.producer_id.split("|")):
        logger.log(
            LogReference.PROCREATE003,
            ods_code_parts=metadata.ods_code_parts,
            producer_id=core_model.producer_id,
        )
        return SpineErrorResponse.BAD_REQUEST(
            diagnostics="The id of the provided DocumentReference does not include the expected ODS code for this organisation"
        )

    custodian_parts = tuple(
        filter(None, (core_model.custodian, core_model.custodian_suffix))
    )
    if metadata.ods_code_parts != custodian_parts:
        logger.log(
            LogReference.PROCREATE004,
            ods_code_parts=metadata.ods_code_parts,
            custodian_parts=custodian_parts,
        )
        return SpineErrorResponse.BAD_REQUEST(
            diagnostics="The custodian of the provided DocumentReference does not match the expected ODS code for this organisation",
            expression="custodian.identifier.value",
        )

    if core_model.type not in metadata.pointer_types:
        logger.log(
            LogReference.PROCREATE005,
            ods_code=metadata.ods_code,
            type=core_model.type,
            pointer_types=metadata.pointer_types,
        )
        return SpineErrorResponse.AUTHOR_CREDENTIALS_ERROR(
            diagnostics="The type of the provided DocumentReference is not in the list of allowed types for this organisation",
            expression="type.coding[0].code",
        )

    ids_to_delete = []

    if result.resource.relatesTo:
        logger.log(LogReference.PROCREATE006, relatesTo=result.resource.relatesTo)

        for idx, relates_to in enumerate(result.resource.relatesTo):
            if not (identifier := getattr(relates_to.target.identifier, "value", None)):
                logger.log(LogReference.PROCREATE007a)
                return SpineErrorResponse.BAD_REQUEST(
                    diagnostics="No identifier value provided for relatesTo target",
                    expression=f"relatesTo[{idx}].target.identifier.value",
                )

            producer_id = identifier.split("-", 1)[0]
            if metadata.ods_code_parts != tuple(producer_id.split("|")):
                logger.log(
                    LogReference.PROCREATE007b,
                    related_identifier=identifier,
                    ods_code_parts=metadata.ods_code_parts,
                )
                return SpineErrorResponse.BAD_REQUEST(
                    diagnostics="The relatesTo target identifier value does not include the expected ODS code for this organisation",
                    expression=f"relatesTo[{idx}].target.identifier.value",
                )

            if not (existing_pointer := repository.get_by_id(identifier)):
                logger.log(LogReference.PROCREATE007c, related_identifier=identifier)
                return SpineErrorResponse.BAD_REQUEST(
                    diagnostics="The relatesTo target document does not exist",
                    expression=f"relatesTo[{idx}].target.identifier.value",
                )

            if existing_pointer.nhs_number != core_model.nhs_number:
                logger.log(LogReference.PROCREATE007d, related_identifier=identifier)
                return SpineErrorResponse.BAD_REQUEST(
                    diagnostics="The relatesTo target document NHS number does not match the NHS number in the request",
                    expression=f"relatesTo[{idx}].target.identifier.value",
                )

            if existing_pointer.type != core_model.type:
                logger.log(LogReference.PROCREATE007e, related_identifier=identifier)
                return SpineErrorResponse.BAD_REQUEST(
                    diagnostics="The relatesTo target document type does not match the type in the request",
                    expression=f"relatesTo[{idx}].target.identifier.value",
                )

            if relates_to.code == "replaces":
                logger.log(
                    LogReference.PROCREATE008,
                    relates_to_code=relates_to.code,
                    identifier=identifier,
                )
                ids_to_delete.append(identifier)

    if ids_to_delete:
        logger.log(
            LogReference.PROCREATE010,
            pointer_id=result.resource.id,
            ids_to_delete=ids_to_delete,
        )
        saved_model = repository.supersede(core_model, ids_to_delete)
        logger.log(LogReference.PROCREATE999)
        return NRLResponse.RESOURCE_SUPERSEDED()

    logger.log(LogReference.PROCREATE009, pointer_id=result.resource.id)
    saved_model = repository.create(core_model)
    logger.log(LogReference.PROCREATE999)
    return NRLResponse.RESOURCE_CREATED()
