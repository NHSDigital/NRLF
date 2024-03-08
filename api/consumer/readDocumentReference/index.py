import urllib.parse
from typing import Dict

from nrlf.core_nonpipeline.decorators import APIGatewayProxyEvent, request_handler
from nrlf.core_nonpipeline.dynamodb.repository import DocumentPointerRepository
from nrlf.producer.fhir.r4.model import DocumentReference


@request_handler()
def handler(
    event: APIGatewayProxyEvent, repository: DocumentPointerRepository, **_
) -> Dict[str, str]:
    """
    Entrypoint for the readDocumentReference function
    """
    subject = (event.path_parameters or {}).get("id", "unknown")
    parsed_id = urllib.parse.unquote(subject)

    result = repository.get_by_id(parsed_id)

    if result is None:
        return {"statusCode": "404", "body": "Not Found"}

    document_reference = DocumentReference.parse_raw(result.document)

    return {
        "statusCode": "200",
        "body": document_reference.json(indent=2, exclude_none=True),
    }
