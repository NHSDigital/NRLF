from nrlf.consumer.fhir.r4.model import Bundle, ExpressionItem, OperationOutcomeIssue
from nrlf.core.codes import SpineErrorConcept
from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.model import ConnectionMetadata, CountRequestParams
from nrlf.core.response import Response


@request_handler(params=CountRequestParams)
def handler(
    metadata: ConnectionMetadata,
    params: CountRequestParams,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Entrypoint for the countDocumentReference function
    """
    if not (nhs_number := params.nhs_number):
        return Response.from_issues(
            statusCode="400",
            issues=[
                OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("INVALID_IDENTIFIER_VALUE"),
                    diagnostics="Invalid NHS number provided in the query parameters",
                    expression=[ExpressionItem(__root__="subject:identifier")],
                )
            ],
        )

    result = repository.count_by_nhs_number(
        nhs_number=nhs_number, pointer_types=metadata.pointer_types
    )

    bundle = Bundle(resourceType="Bundle", type="searchset", total=result)
    return Response.from_bundle(bundle)
