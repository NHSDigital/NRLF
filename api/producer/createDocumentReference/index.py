from nrlf.core.codes import NRLResponseConcept, SpineErrorConcept
from nrlf.core.decorators import request_handler
from nrlf.core.dynamodb.repository import DocumentPointer, DocumentPointerRepository
from nrlf.core.model import ConnectionMetadata
from nrlf.core.response import Response
from nrlf.core.validators import DocumentReferenceValidator
from nrlf.producer.fhir.r4.model import (
    DocumentReference,
    ExpressionItem,
    OperationOutcomeIssue,
)


@request_handler(body=DocumentReference)
def handler(
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    body: DocumentReference,
) -> Response:
    """
    Entrypoint for the createDocumentReference function
    """
    validator = DocumentReferenceValidator()

    result = validator.validate(body)
    if not result.is_valid:
        return Response.from_issues(issues=result.issues, statusCode="400")

    core_model = DocumentPointer.from_document_reference(result.resource)

    if metadata.ods_code_parts != tuple(core_model.producer_id.split("|")):
        return Response.from_issues(
            statusCode="400",
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("BAD_REQUEST"),
                    diagnostics="The id of the provided document pointer does not include the expected organisation code for this app",
                )
            ],
        )

    custodian_parts = tuple(
        filter(None, (core_model.custodian, core_model.custodian_suffix))
    )
    if metadata.ods_code_parts != custodian_parts:
        return Response.from_issues(
            statusCode="400",
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("BAD_REQUEST"),
                    diagnostics="The custodian of the provided document pointer does not match the expected organisation code for this app",
                    expression=[ExpressionItem(__root__="custodian.identifier.value")],
                )
            ],
        )

    if core_model.type not in metadata.pointer_types:
        return Response.from_issues(
            statusCode="401",
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("AUTHOR_CREDENTIALS_ERROR"),
                    diagnostics="The type of the provided document pointer is not in the list of allowed types for this app",
                    expression=[ExpressionItem(__root__="type.coding[0].code")],
                )
            ],
        )

    ids_to_delete = []

    if result.resource.relatesTo:
        for idx, relates_to in enumerate(result.resource.relatesTo):
            if not (identifier := getattr(relates_to.target.identifier, "value", None)):
                return Response.from_issues(
                    issues=[
                        OperationOutcomeIssue(
                            severity="error",
                            code="invalid",
                            details=SpineErrorConcept.from_code("BAD_REQUEST"),
                            diagnostics="No identifier value provided for relatesTo target",
                            expression=[
                                ExpressionItem(
                                    __root__=f"relatesTo[{idx}].target.identifier.value"
                                )
                            ],
                        )
                    ],
                    statusCode="400",
                )

            producer_id = identifier.split("-", 1)[0]
            if metadata.ods_code_parts != tuple(producer_id.split("|")):
                return Response.from_issues(
                    statusCode="400",
                    issues=[
                        OperationOutcomeIssue(
                            severity="error",
                            code="invalid",
                            details=SpineErrorConcept.from_code("BAD_REQUEST"),
                            diagnostics="The relatesTo target identifier value does not include the expected organisation code for this app",
                            expression=[
                                ExpressionItem(
                                    __root__=f"relatesTo[{idx}].target.identifier.value"
                                )
                            ],
                        )
                    ],
                )

            if not (pointer := repository.get_by_id(identifier)):
                return Response.from_issues(
                    statusCode="400",
                    issues=[
                        OperationOutcomeIssue(
                            severity="error",
                            code="invalid",
                            details=SpineErrorConcept.from_code("BAD_REQUEST"),
                            diagnostics="The relatesTo target document does not exist",
                            expression=[
                                ExpressionItem(
                                    __root__=f"relatesTo[{idx}].target.identifier.value"
                                )
                            ],
                        )
                    ],
                )

            if pointer.nhs_number != core_model.nhs_number:
                return Response.from_issues(
                    statusCode="400",
                    issues=[
                        OperationOutcomeIssue(
                            severity="error",
                            code="invalid",
                            details=SpineErrorConcept.from_code("BAD_REQUEST"),
                            diagnostics="The relatesTo target document NHS number does not match the NHS number in the request",
                            expression=[
                                ExpressionItem(
                                    __root__=f"relatesTo[{idx}].target.identifier.value"
                                )
                            ],
                        )
                    ],
                )

            if pointer.type != core_model.type:
                return Response.from_issues(
                    statusCode="400",
                    issues=[
                        OperationOutcomeIssue(
                            severity="error",
                            code="invalid",
                            details=SpineErrorConcept.from_code("BAD_REQUEST"),
                            diagnostics="The relatesTo target document type does not match the type in the request",
                            expression=[
                                ExpressionItem(
                                    __root__=f"relatesTo[{idx}].target.identifier.value"
                                )
                            ],
                        )
                    ],
                )

            if relates_to.code == "replaces":
                ids_to_delete.append(identifier)

    if ids_to_delete:
        saved_model = repository.supersede(core_model, ids_to_delete)
        return Response.from_issues(
            issues=[
                OperationOutcomeIssue(
                    severity="information",
                    code="informational",
                    details=NRLResponseConcept.from_code("RESOURCE_SUPERSEDED"),
                    diagnostics="The document has been superseded by a new version",
                )
            ],
            statusCode="201",
        )

    saved_model = repository.create(core_model)
    return Response.from_issues(
        issues=[
            OperationOutcomeIssue(
                severity="information",
                code="informational",
                details=NRLResponseConcept.from_code("RESOURCE_CREATED"),
                diagnostics="The document has been created",
            )
        ],
        statusCode="201",
    )
