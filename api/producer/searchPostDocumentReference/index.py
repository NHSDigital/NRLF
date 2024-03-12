from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.model import ConnectionMetadata, ProducerRequestParams
from nrlf.core.response import Response, SpineErrorConcept
from nrlf.core.validators import validate_type_system
from nrlf.producer.fhir.r4.model import Bundle, DocumentReference, OperationOutcomeIssue


@request_handler(body=ProducerRequestParams)
def handler(
    body: ProducerRequestParams,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Entrypoint for the searchDocumentReference function
    """
    if not body.nhs_number:
        return Response.from_issues(
            statusCode="400",
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="bad-request",
                    details=SpineErrorConcept.from_code("INVALID_NHS_NUMBER"),
                    diagnostics="NHS number is required to search for document references",
                )
            ],
        )

    if not validate_type_system(body.type, metadata.pointer_types):
        return Response.from_issues(
            statusCode="400",
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="bad-request",
                    details=SpineErrorConcept.from_code("INVALID_CODE_SYSTEM"),
                    diagnostics="The provided system type value does not match the allowed types",
                )
            ],
        )

    pointer_types = metadata.pointer_types
    if body.type:
        pointer_types = [str(body.type)]

    bundle = {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}

    for result in repository.search_by_custodian(
        custodian=metadata.ods_code,
        custodian_suffix=metadata.ods_code_extension,
        nhs_number=body.nhs_number,
        pointer_types=pointer_types,
    ):
        document_reference = DocumentReference.parse_raw(result.document)
        bundle["total"] += 1
        bundle["entry"].append({"resource": document_reference.dict(exclude_none=True)})

    return Response.from_bundle(Bundle.parse_obj(bundle))
