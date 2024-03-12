from nrlf.consumer.fhir.r4.model import Bundle, DocumentReference, OperationOutcomeIssue
from nrlf.core.decorators import request_handler
from nrlf.core.dynamodb.repository import DocumentPointerRepository
from nrlf.core.model import ConnectionMetadata, ConsumerRequestParams
from nrlf.core.response import Response, SpineErrorConcept
from nrlf.core.validators import validate_type_system


@request_handler(body=ConsumerRequestParams)
def handler(
    body: ConsumerRequestParams,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Entrypoint for the readDocumentReference function
    """
    if not body.nhs_number:
        return Response.from_issues(
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("INVALID_NHS_NUMBER"),
                    diagnostics="A valid NHS number is required to search for document references",
                )
            ],
            statusCode="400",
        )

    if not validate_type_system(body.type, metadata.pointer_types):
        return Response.from_issues(
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("INVALID_CODE_VALUE"),
                    diagnostics="The provided system type value does not match the allowed types",
                )
            ],
            statusCode="400",
        )

    bundle = {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}

    pointer_types = [body.type.__root__] if body.type else metadata.pointer_types

    for result in repository.search(body.nhs_number, pointer_types):
        document_reference = DocumentReference.parse_raw(result.document)
        bundle["total"] += 1
        bundle["entry"].append({"resource": document_reference.dict(exclude_none=True)})

    return Response.from_bundle(Bundle.parse_obj(bundle))
