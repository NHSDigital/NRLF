import json
from typing import Dict, Type

from pydantic import BaseModel, ValidationError

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.constants import CLIENT_RP_DETAILS, CONNECTION_METADATA
from nrlf.core.errors import OperationOutcomeError, ParseError
from nrlf.core.logger import LogReference, logger
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

        client_rp_details = ClientRpDetails.model_validate(raw_client_rp_details)
        return ConnectionMetadata.model_validate(
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
    model: Type[BaseModel] | None,
    query_string_params: Dict[str, str] | None,
) -> BaseModel | None:
    if not model:
        return None

    logger.log(
        LogReference.HANDLER006,
        params=query_string_params,
        model=model.__name__,
    )

    try:
        result = model.model_validate(query_string_params or {})
        logger.log(LogReference.HANDLER007, parsed_params=result.model_dump())
        return result

    except ValidationError as exc:
        raise ParseError.from_validation_error(
            exc,
            details=SpineErrorConcept.from_code("INVALID_PARAMETER"),
            msg="Invalid query parameter",
        ) from None


def parse_body(
    model: Type[BaseModel] | None,
    body: str | None,
) -> BaseModel | None:
    if not model:
        return None

    logger.log(LogReference.HANDLER008, body=body, model=model.__name__)

    if not body:
        raise OperationOutcomeError(
            status_code="400",
            severity="error",
            code="invalid",
            details=SpineErrorConcept.from_code("BAD_REQUEST"),
            diagnostics="Request body is required",
        )

    try:
        result = model.model_validate_json(body)
        logger.log(LogReference.HANDLER009, parsed_body=result.model_dump())
        return result

    except ValidationError as exc:
        raise ParseError.from_validation_error(
            exc,
            details=SpineErrorConcept.from_code("MESSAGE_NOT_WELL_FORMED"),
            msg="Request body could not be parsed",
        ) from None


def parse_path(
    model: Type[BaseModel] | None,
    path_params: Dict[str, str] | None,
) -> BaseModel | None:
    if not model:
        return None

    logger.log(
        LogReference.HANDLER010,
        path=path_params,
        model=model.__name__,
    )

    try:
        result = model.model_validate(path_params or {})
        logger.log(LogReference.HANDLER011, parsed_path=result.model_dump())
        return result

    except ValidationError as exc:
        raise ParseError.from_validation_error(
            exc,
            details=SpineErrorConcept.from_code("INVALID_PARAMETER"),
            msg="Invalid path parameter",
        ) from None
