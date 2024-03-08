from typing import Dict, List

from nrlf.core.model import ProducerRequestParams
from nrlf.core_nonpipeline.decorators import (
    ConnectionMetadata,
    DocumentPointerRepository,
    request_handler,
)
from nrlf.producer.fhir.r4.model import Bundle, DocumentReference, RequestQueryType


def validate_type_system(type_: RequestQueryType, pointer_types: List[str]):
    if not type_:
        return

    type_system = type_.__root__.split("|", 1)[0]

    pointer_type_systems = [
        pointer_type.split("|", 1)[0] for pointer_type in pointer_types
    ]

    if type_system not in pointer_type_systems:
        # TODO: Original AuthenticationError
        raise ValueError(
            f"The provided system type value - {type_system} - does not match the allowed types"
        )


@request_handler(body=ProducerRequestParams)
def handler(
    body: ProducerRequestParams,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    **_,
) -> Dict[str, str]:
    """
    Entrypoint for the searchDocumentReference function
    """
    if not body.nhs_number:
        return {"statusCode": "400", "body": "Bad Request"}

    if body.type:
        validate_type_system(body.type, metadata.pointer_types)

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

    return {
        "statusCode": "200",
        "body": Bundle(**bundle).json(
            indent=2, exclude_none=True, exclude_defaults=True
        ),
    }
