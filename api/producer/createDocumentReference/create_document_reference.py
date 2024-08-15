from uuid import uuid4

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.constants import (
    PERMISSION_AUDIT_DATES_FROM_PAYLOAD,
    PERMISSION_SUPERSEDE_IGNORE_DELETE_FAIL,
    TYPE_CATEGORIES,
)
from nrlf.core.decorators import request_handler
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.core.errors import OperationOutcomeError
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata
from nrlf.core.response import NRLResponse, Response, SpineErrorResponse
from nrlf.core.utils import create_fhir_instant
from nrlf.core.validators import DocumentReferenceValidator
from nrlf.producer.fhir.r4.model import DocumentReference, Meta


def _set_create_time_fields(
    create_time: str, document_reference: DocumentReference, nrl_permissions: list[str]
) -> DocumentReference:
    """
    Set the date and lastUpdated timestamps on the provided DocumentReference
    """
    if not document_reference.meta:
        document_reference.meta = Meta()
    document_reference.meta.lastUpdated = create_time

    if (
        document_reference.date
        and PERMISSION_AUDIT_DATES_FROM_PAYLOAD in nrl_permissions
    ):
        # Perserving the original date if it exists and the permission is set
        logger.log(
            LogReference.PROCREATE011,
            id=document_reference.id,
            date=document_reference.date,
        )
    else:
        document_reference.date = create_time

    return document_reference


def _create_core_model(resource: DocumentReference, metadata: ConnectionMetadata):
    """
    Create the DocumentPointer model from the provided DocumentReference
    """
    creation_time = create_fhir_instant()
    document_reference = _set_create_time_fields(
        creation_time,
        document_reference=resource,
        nrl_permissions=metadata.nrl_permissions,
    )

    return DocumentPointer.from_document_reference(
        document_reference, created_on=creation_time
    )


def _check_permissions(
    core_model: DocumentPointer, metadata: ConnectionMetadata
) -> Response | None:
    """
    Check the requester has permissions to create the DocumentReference
    """
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

    type_category = TYPE_CATEGORIES.get(core_model.type)
    if type_category != core_model.category:
        logger.log(
            LogReference.PROCREATE005a,
            ods_code=metadata.ods_code,
            type=core_model.type,
            category=core_model.category,
        )
        return SpineErrorResponse.BAD_REQUEST(
            diagnostics=f"The Category code of the provided document '{core_model.category}' must match the allowed category for pointer type '{core_model.type}' with a category value of '{type_category}'",
            expression="category.coding[0].code",
        )


def _get_document_ids_to_supersede(
    resource: DocumentReference,
    core_model: DocumentPointer,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    can_ignore_delete_fail: bool,
):
    """
    Get the list of document IDs to supersede based on the relatesTo field
    """
    if not resource.relatesTo:
        return []

    logger.log(LogReference.PROCREATE006, relatesTo=resource.relatesTo)
    ids_to_delete = []

    for idx, relates_to in enumerate(resource.relatesTo):
        identifier = _validate_identifier(relates_to, idx)
        _validate_producer_id(identifier, metadata, idx)

        if not can_ignore_delete_fail:
            existing_pointer = _check_existing_pointer(identifier, repository, idx)
            _validate_pointer_details(existing_pointer, core_model, identifier, idx)

        _append_id_if_replaces(relates_to, ids_to_delete, identifier)

    return ids_to_delete


def _validate_identifier(relates_to, idx):
    """
    Validate that there is a identifier in relatesTo target
    """
    identifier = getattr(relates_to.target.identifier, "value", None)
    if not identifier:
        logger.log(LogReference.PROCREATE007a)
        _raise_operation_outcome_error(
            "No identifier value provided for relatesTo target", idx
        )
    return identifier


def _validate_producer_id(identifier, metadata, idx):
    """
    Validate that there is an ODS code in the relatesTo target identifier
    """
    producer_id = identifier.split("-", 1)[0]
    if metadata.ods_code_parts != tuple(producer_id.split("|")):
        logger.log(
            LogReference.PROCREATE007b,
            related_identifier=identifier,
            ods_code_parts=metadata.ods_code_parts,
        )
        _raise_operation_outcome_error(
            "The relatesTo target identifier value does not include the expected ODS code for this organisation",
            idx,
        )


def _check_existing_pointer(identifier, repository, idx):
    """
    Check that there is an existing pointer that will be deleted when superseding
    """
    existing_pointer = repository.get_by_id(identifier)
    if not existing_pointer:
        logger.log(LogReference.PROCREATE007c, related_identifier=identifier)
        _raise_operation_outcome_error(
            "The relatesTo target document does not exist", idx
        )
    return existing_pointer


def _validate_pointer_details(existing_pointer, core_model, identifier, idx):
    """
    Validate that the nhs numbers and type matches between the existing pointer and the requested one.
    """
    if existing_pointer.nhs_number != core_model.nhs_number:
        logger.log(LogReference.PROCREATE007d, related_identifier=identifier)
        _raise_operation_outcome_error(
            "The relatesTo target document NHS number does not match the NHS number in the request",
            idx,
        )

    if existing_pointer.type != core_model.type:
        logger.log(LogReference.PROCREATE007e, related_identifier=identifier)
        _raise_operation_outcome_error(
            "The relatesTo target document type does not match the type in the request",
            idx,
        )


def _append_id_if_replaces(relates_to, ids_to_delete, identifier):
    """
    Append pointer ID if the if the relatesTo code is 'replaces'
    """
    if relates_to.code == "replaces":
        logger.log(
            LogReference.PROCREATE008,
            relates_to_code=relates_to.code,
            identifier=identifier,
        )
        ids_to_delete.append(identifier)


def _raise_operation_outcome_error(diagnostics, idx):
    """
    General function to raise an operation outcome error
    """
    raise OperationOutcomeError(
        severity="error",
        code="invalid",
        details=SpineErrorConcept.from_code("BAD_REQUEST"),
        diagnostics=diagnostics,
        expression=[f"relatesTo[{idx}].target.identifier.value"],
    )


@request_handler(body=DocumentReference)
def handler(
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    body: DocumentReference,
) -> Response:
    """
    Creates a document reference.

    Args:
        metadata (ConnectionMetadata): The connection metadata.
        repository (DocumentPointerRepository): The document pointer repository.
        body (DocumentReference): The document reference to create.

    Returns:
        Response: The response indicating the result of the operation.
    """
    logger.log(LogReference.PROCREATE000)
    logger.log(LogReference.PROCREATE001, resource=body)

    id_prefix = "|".join(metadata.ods_code_parts)
    body.id = f"{id_prefix}-{uuid4()}"

    validator = DocumentReferenceValidator()
    result = validator.validate(body)

    if not result.is_valid:
        logger.log(LogReference.PROCREATE002)
        return Response.from_issues(issues=result.issues, statusCode="400")

    core_model = _create_core_model(result.resource, metadata)
    if error_response := _check_permissions(core_model, metadata):
        return error_response

    can_ignore_delete_fail = (
        PERMISSION_SUPERSEDE_IGNORE_DELETE_FAIL in metadata.nrl_permissions
    )

    if ids_to_delete := _get_document_ids_to_supersede(
        result.resource, core_model, metadata, repository, can_ignore_delete_fail
    ):
        logger.log(
            LogReference.PROCREATE010,
            pointer_id=result.resource.id,
            ids_to_delete=ids_to_delete,
        )
        repository.supersede(core_model, ids_to_delete, can_ignore_delete_fail)
        logger.log(LogReference.PROCREATE999)
        return NRLResponse.RESOURCE_SUPERSEDED(resource_id=result.resource.id)

    logger.log(LogReference.PROCREATE009, pointer_id=result.resource.id)
    repository.create(core_model)
    logger.log(LogReference.PROCREATE999)
    return NRLResponse.RESOURCE_CREATED(resource_id=result.resource.id)
