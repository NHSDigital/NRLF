from typing import Dict

from nrlf.core_nonpipeline.decorators import (
    APIGatewayProxyEvent,
    ConnectionMetadata,
    request_handler,
)
from nrlf.core_nonpipeline.dynamodb.repository import (
    DocumentPointer,
    DocumentPointerRepository,
)
from nrlf.core_nonpipeline.errors import OperationOutcomeResponse
from nrlf.core_nonpipeline.logger import logger
from nrlf.core_nonpipeline.transform import DocumentReferenceValidator, ParseError
from nrlf.producer.fhir.r4.model import (
    CodeableConcept,
    Coding,
    OperationOutcome,
    OperationOutcomeIssue,
)


@request_handler()
def handler(
    event: APIGatewayProxyEvent,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    **_,
) -> Dict[str, str]:
    """
    Entrypoint for the createDocumentReference function
    """
    if not event.body:
        return {"statusCode": "400", "body": "Bad Request"}

    body = event.json_body
    validator = DocumentReferenceValidator()

    try:
        result = validator.validate(body)

    except ParseError as error:
        raise OperationOutcomeResponse(issues=error.issues)

    if not result.is_valid:
        logger.debug(result)
        raise OperationOutcomeResponse(issues=result.issues)

    # TODO: Do data contract validation here

    core_model = DocumentPointer.from_document_reference(result.resource)

    if metadata.ods_code_parts != tuple(core_model.producer_id.split("|")):
        # TODO: ProducerValidationError
        raise Exception(
            "The id of the provided document pointer does not include the expected organisation code for this app"
        )

    custodian_parts = tuple(
        filter(None, (core_model.custodian, core_model.custodian_suffix))
    )
    if metadata.ods_code_parts != custodian_parts:
        raise Exception(
            "The custodian of the provided document pointer does not match the expected organisation code for this app"
        )

    if core_model.type not in metadata.pointer_types:
        raise Exception(
            "The type of the provided document pointer is in the list of allowed types for this app"
        )

    if result.resource.relatesTo:
        superseded_ids = []

        for relates_to in result.resource.relatesTo:
            if not (identifier := getattr(relates_to.target, "identifier", None)):
                raise Exception("No identifier provider for supersede target")

            producer_id = identifier.split("-", 1)[0]
            if metadata.ods_code_parts != tuple(producer_id.split("|")):
                raise Exception(
                    "At least one document pointer cannot be deleted because it belongs to another organisation"
                )

            if not (pointer := repository.get_by_id(identifier)):
                # Original - SupersedeValidationError
                raise Exception(
                    "Validation failure - relatesTo target document does not exist"
                )

            if pointer.nhs_number != core_model.nhs_number:
                raise Exception(
                    "Validation failure - relatesTo target document nhs number does not match the request"
                )

            if pointer.type != core_model.type:
                raise Exception(
                    "Validation failure - relatesTo target document type does not match the request"
                )

            superseded_ids.append(identifier)

        result = repository.supersede(core_model, superseded_ids)

        operation_outcome = OperationOutcome(
            resourceType="OperationOutcome",
            issue=[
                OperationOutcomeIssue(
                    severity="information",
                    code="informational",
                    details=CodeableConcept(
                        coding=[
                            Coding(
                                system="https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                                code="RESOURCE_SUPERSEDED",
                                display="Resource created and resources(s) deleted",
                            )
                        ]
                    ),
                )
            ],
        )

        return {
            "statusCode": "201",
            "body": operation_outcome.json(indent=2, exclude_none=True),
        }

    saved_model = repository.create(core_model)
    operation_outcome = OperationOutcome(
        resourceType="OperationOutcome",
        issue=[
            OperationOutcomeIssue(
                severity="information",
                code="informational",
                details=CodeableConcept(
                    coding=[
                        Coding(
                            system="https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                            code="RESOURCE_CREATED",
                            display="Resource created",
                        )
                    ]
                ),
            )
        ],
    )

    return {
        "statusCode": "201",
        "body": operation_outcome.json(indent=2, exclude_none=True),
    }
