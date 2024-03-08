from typing import Dict, List

from nrlf.consumer.fhir.r4.model import Bundle, RequestQueryType
from nrlf.core.model import ConsumerRequestParams
from nrlf.core_nonpipeline.decorators import ConnectionMetadata, request_handler
from nrlf.core_nonpipeline.dynamodb.repository import DocumentPointerRepository
from nrlf.producer.fhir.r4.model import DocumentReference


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


@request_handler(body=ConsumerRequestParams)
def handler(
    body: ConsumerRequestParams,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    **_,
) -> Dict[str, str]:
    """
    Entrypoint for the readDocumentReference function
    """
    if not body.nhs_number:
        return {"statusCode": "400", "body": "Bad Request"}

    if body.type:
        validate_type_system(body.type, metadata.pointer_types)

    bundle = {"resourceType": "Bundle", "type": "searchset", "total": 0, "entry": []}

    pointer_types = [str(body.type)] if body.type else metadata.pointer_types

    for result in repository.search(body.nhs_number, pointer_types):
        document_reference = DocumentReference.parse_raw(result.document)
        bundle["total"] += 1
        bundle["entry"].append({"resource": document_reference.dict(exclude_none=True)})

    return {
        "statusCode": "200",
        "body": Bundle(**bundle).json(
            indent=2, exclude_none=True, exclude_defaults=True
        ),
    }
