import urllib.parse
from typing import Dict

from nrlf.core_nonpipeline.decorators import (
    APIGatewayProxyEvent,
    ConnectionMetadata,
    DocumentPointerRepository,
    request_handler,
)
from nrlf.producer.fhir.r4.model import (
    CodeableConcept,
    Coding,
    OperationOutcome,
    OperationOutcomeIssue,
)


@request_handler()
def handler(
    event: APIGatewayProxyEvent,
    metadata: ConnectionMetadata,
    repository: DocumentPointerRepository,
    **_,
) -> Dict[str, str]:
    """
    Entrypoint for the deleteDocumentReference function
    """
    pointer_id = urllib.parse.unquote(
        (event.path_parameters or {}).get("id", "unknown")
    )
    producer_id, _ = pointer_id.split("-", 1)

    if metadata.ods_code_parts != tuple(producer_id.split(".")):
        raise Exception(
            "The requested document pointer cannot be deleted because it belongs to another organisation"
        )

    if not (core_model := repository.get_by_id(pointer_id)):
        raise Exception("Item could not be found")

    repository.delete(core_model)
    operation_outcome = OperationOutcome(
        resourceType="OperationOutcome",
        issue=[
            OperationOutcomeIssue(
                severity="information",
                code="informational",
                details=CodeableConcept(
                    coding=[
                        Coding(
                            system="https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
                            code="RESOURCE_DELETED",
                            display="Resource deleted",
                        )
                    ]
                ),
            )
        ],
    )

    return {
        "statusCode": "200",
        "body": operation_outcome.json(exclude_none=True, indent=2),
    }
