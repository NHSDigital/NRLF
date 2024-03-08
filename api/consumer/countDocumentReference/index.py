from nhs_number import is_valid as is_valid_nhs_number
from pydantic import BaseModel, Field, validator

from nrlf.consumer.fhir.r4.model import Bundle
from nrlf.core.decorators import DocumentPointerRepository, request_handler
from nrlf.core.model import ConnectionMetadata
from nrlf.core.response import Response


class CountRequestParams(BaseModel):
    nhs_number: str = Field(alias="subject:identifier")

    @validator("nhs_number", pre=True)
    def validate_nhs_number(cls, nhs_number: str):
        nhs_number = nhs_number.split("|", 1)[1]
        if not is_valid_nhs_number(nhs_number):
            raise ValueError("Invalid NHS number")

        return nhs_number


@request_handler(params=CountRequestParams)
def handler(
    metadata: ConnectionMetadata,
    params: CountRequestParams,
    repository: DocumentPointerRepository,
) -> Response:
    """
    Entrypoint for the countDocumentReference function
    """
    result = repository.count_by_nhs_number(
        nhs_number=params.nhs_number, pointer_types=metadata.pointer_types
    )

    bundle = Bundle(resourceType="Bundle", type="searchset", total=result)
    return Response.from_bundle(bundle)
