import json

from lambda_utils.constants import HttpStatusCodes
from nrlf.producer.fhir.r4.model import OperationOutcome, OperationOutcomeIssue
from pydantic import ValidationError


def _operation_outcome(code: str, severity: str, msg: str) -> dict:
    return OperationOutcome(
        resourceType="OperationOutcome",
        issue=[OperationOutcomeIssue(code=code, severity=severity, diagnostics=msg)],
    ).dict(exclude_none=True)


def _error(msg: str) -> dict:
    return _operation_outcome("processing", "error", msg)


def ok(msg: str) -> tuple[int, dict]:
    return HttpStatusCodes.OK, _operation_outcome("processing", "success", msg)


def bad_request(msg: str) -> tuple[int, dict]:
    return HttpStatusCodes.BAD_REQUEST, _error(msg)


def internal_server_error() -> tuple[int, dict]:
    return HttpStatusCodes.INTERNAL_SERVER_ERROR, _error("Internal server error")


def get_error_msg(error: ValidationError) -> str:
    errors = json.loads(error.json())
    first_error = errors[0]
    try:
        error_msg_prefix = f"{error.model.public_alias()} validation failure"
    except:
        error_msg_prefix = f"{error.model.__name__} validation failure"

    if first_error["type"] == "value_error":
        return f'{error_msg_prefix} - Invalid {first_error["loc"][0]} - {first_error["msg"]}'
    return f'{error_msg_prefix} - Invalid {first_error["loc"][0]}'
