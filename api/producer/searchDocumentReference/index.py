from typing import List, Optional

from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.model import ConnectionMetadata, ProducerRequestParams
from nrlf.core.response import Response, SpineErrorConcept
from nrlf.producer.fhir.r4.model import (
    Bundle,
    DocumentReference,
    OperationOutcomeIssue,
    RequestQueryType,
)


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


@request_handler(params=ProducerRequestParams)
def handler(
    metadata: ConnectionMetadata,
    params: ProducerRequestParams,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Entrypoint for the searchDocumentReference function
    """
    if not params.nhs_number:
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

    if not validate_type_system(params.type, metadata.pointer_types):
        return Response.from_issues(
            statusCode=200,
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
    if params.type:
        pointer_types = [str(params.type)]

    bundle = {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}

    for result in repository.search_by_custodian(
        custodian=metadata.ods_code,
        custodian_suffix=metadata.ods_code_extension,
        nhs_number=params.nhs_number,
        pointer_types=pointer_types,
    ):
        document_reference = DocumentReference.parse_raw(result.document)
        bundle["total"] += 1
        bundle["entry"].append({"resource": document_reference.dict(exclude_none=True)})

    return Response.from_bundle(Bundle.parse_obj(bundle))
