from typing import List, Optional

from nrlf.consumer.fhir.r4.model import (
    Bundle,
    DocumentReference,
    OperationOutcomeIssue,
    RequestQueryType,
)
from nrlf.core.decorators import request_handler
from nrlf.core.dynamodb.repository import DocumentPointerRepository
from nrlf.core.model import ConnectionMetadata, ConsumerRequestParams
from nrlf.core.response import Response, SpineErrorConcept


def validate_type_system(
    type_: Optional[RequestQueryType], pointer_types: List[str]
) -> bool:
    """
    Validates if the given type system is present in the list of pointer types.
    """
    if not type_:
        return True

    type_system = str(type_).split("|", 1)[0]
    pointer_type_systems = [
        pointer_type.split("|", 1)[0] for pointer_type in pointer_types
    ]

    return type_system in pointer_type_systems


@request_handler(params=ConsumerRequestParams)
def handler(
    metadata: ConnectionMetadata,
    params: ConsumerRequestParams,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Entrypoint for the readDocumentReference function
    """
    if not params.nhs_number:
        return Response.from_issues(
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="bad-request",
                    details=SpineErrorConcept.from_code("INVALID_NHS_NUMBER"),
                    diagnostics="NHS number is required to search for document references",
                )
            ],
            statusCode="400",
        )

    if not validate_type_system(params.type, metadata.pointer_types):
        return Response.from_issues(
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="bad-request",
                    details=SpineErrorConcept.from_code("INVALID_CODE_SYSTEM"),
                    diagnostics="The provided system type value does not match the allowed types",
                )
            ],
            statusCode="400",
        )

    bundle = {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}

    for result in repository.search(params.nhs_number):
        document_reference = DocumentReference.parse_obj(result.document)
        bundle["total"] += 1
        bundle["entry"].append({"resource": document_reference.dict(exclude_none=True)})

    return Response.from_bundle(Bundle.parse_obj(bundle))
