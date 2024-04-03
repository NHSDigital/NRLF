import json
from typing import Dict, Type

from pydantic.v1 import BaseModel, ValidationError

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.constants import CLIENT_RP_DETAILS, CONNECTION_METADATA
from nrlf.core.errors import OperationOutcomeError, ParseError
from nrlf.core.model import ClientRpDetails, ConnectionMetadata


def parse_headers(headers: Dict[str, str]) -> ConnectionMetadata:
    """
    Parses the connection metadata and client rp details from the headers passed from Apigee
    """
    case_insensitive_headers = {key.lower(): value for key, value in headers.items()}

    try:
        raw_connection_metadata = json.loads(
            case_insensitive_headers.get(CONNECTION_METADATA, "{}")
        )
        raw_client_rp_details = json.loads(
            case_insensitive_headers.get(CLIENT_RP_DETAILS, "{}")
        )

        client_rp_details = ClientRpDetails.parse_obj(raw_client_rp_details)
        return ConnectionMetadata.parse_obj(
            {**raw_connection_metadata, "client_rp_details": client_rp_details}
        )

    except (ValidationError, json.JSONDecodeError):
        raise OperationOutcomeError(
            status_code="401",
            severity="error",
            code="invalid",
            details=SpineErrorConcept.from_code("MISSING_OR_INVALID_HEADER"),
            diagnostics=(
                "Unable to parse metadata about the requesting application. "
                "Contact the onboarding team."
            ),
        ) from None


def parse_params(
    model: Type[BaseModel],
    query_string_params: Dict[str, str] | None,
):
    try:
        return model.parse_obj(query_string_params or {})
    except ValidationError as exc:
        raise ParseError.from_validation_error(
            exc,
            details=SpineErrorConcept.from_code("INVALID_PARAMETER"),
            msg="Invalid query parameter",
        ) from None


def parse_body(
    model: Type[BaseModel],
    body: str | None,
):
    if not body:
        raise OperationOutcomeError(
            status_code="400",
            severity="error",
            code="invalid",
            details=SpineErrorConcept.from_code("BAD_REQUEST"),
            diagnostics="Request body is required",
        )

    try:
        return model.parse_raw(body)
    except ValidationError as exc:
        raise ParseError.from_validation_error(
            exc,
            details=SpineErrorConcept.from_code("MESSAGE_NOT_WELL_FORMED"),
            msg="Request body could not be parsed",
        ) from None


def parse_path(
    model: Type[BaseModel],
    path_params: Dict[str, str] | None,
):
    try:
        return model.parse_obj(path_params or {})
    except ValidationError as exc:
        raise ParseError.from_validation_error(
            exc,
            details=SpineErrorConcept.from_code("INVALID_PARAMETER"),
            msg="Invalid path parameter",
        ) from None
