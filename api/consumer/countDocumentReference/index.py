from nrlf.consumer.fhir.r4.model import Bundle
from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata, CountRequestParams
from nrlf.core.response import Response, SpineErrorResponse


@request_handler(params=CountRequestParams)
def handler(
    metadata: ConnectionMetadata,
    params: CountRequestParams,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Entrypoint for the countDocumentReference function
    """
    logger.log(LogReference.CONCOUNT000)

    if not (nhs_number := params.nhs_number):
        logger.log(
            LogReference.CONCOUNT001, subject_identifier=params.subject_identifier
        )
        return SpineErrorResponse.INVALID_IDENTIFIER_VALUE(
            diagnostics="Invalid NHS number provided in the query parameters",
            expression="subject:identifier",
        )

    total = repository.count_by_nhs_number(
        nhs_number=nhs_number, pointer_types=metadata.pointer_types
    )

    bundle = Bundle(resourceType="Bundle", type="searchset", total=total)
    response = Response.from_resource(bundle)

    logger.log(LogReference.CONCOUNT999)
    return response
