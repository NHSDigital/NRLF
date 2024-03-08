import json
from typing import Dict

from nrlf.core.constants import CLIENT_RP_DETAILS, CONNECTION_METADATA
from nrlf.core.logger import logger
from nrlf.core.model import ClientRpDetails, ConnectionMetadata


def parse_headers(headers: Dict[str, str]) -> ConnectionMetadata:
    """
    Parses the connection metadata and client rp details from the headers passed from Apigee
    """
    logger.debug("Parsing headers", headers=headers)

    case_insensitive_headers = {key.lower(): value for key, value in headers.items()}

    raw_connection_metadata = json.loads(
        case_insensitive_headers.get(CONNECTION_METADATA, "{}")
    )
    raw_client_rp_details = json.loads(
        case_insensitive_headers.get(CLIENT_RP_DETAILS, "{}")
    )

    client_rp_details = ClientRpDetails.parse_obj(raw_client_rp_details)
    connection_metadata = ConnectionMetadata.parse_obj(
        {**raw_connection_metadata, "client_rp_details": client_rp_details}
    )

    logger.info("Parsed headers", connection_metadata=connection_metadata)

    return connection_metadata
