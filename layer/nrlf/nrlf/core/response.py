from http import HTTPStatus

from nrlf.core.errors import NRLF_TO_SPINE_4XX_ERROR
from nrlf.core.nhsd_codings import (
    META,
    IssueSeverity,
    IssueType,
    NrlfCoding,
    SpineCoding,
)
from nrlf.core.validators import json_loads
from nrlf.producer.fhir.r4.model import (
    CodeableConcept,
    Coding,
    OperationOutcome,
    OperationOutcomeIssue,
)
from pydantic import BaseModel, ValidationError

HTTP_STATUS_CODE_MAPPING = {
    SpineCoding.RESOURCE_NOT_FOUND: HTTPStatus.NOT_FOUND,
    SpineCoding.VALIDATION_ERROR: HTTPStatus.BAD_REQUEST,
    SpineCoding.NOT_ACCEPTABLE: HTTPStatus.FORBIDDEN,
    SpineCoding.MISSING_HEADER: HTTPStatus.BAD_REQUEST,
    SpineCoding.MISSING_VALUE: HTTPStatus.BAD_REQUEST,
    SpineCoding.ACCESS_DENIED_LEVEL: HTTPStatus.FORBIDDEN,
    SpineCoding.SERVICE_ERROR: HTTPStatus.INTERNAL_SERVER_ERROR,
    SpineCoding.INVALID_RESOURCE_ID: HTTPStatus.BAD_REQUEST,
}


class Response(BaseModel):
    status_code: int
    result: dict


def _get_error_from_exception(exception: Exception) -> tuple[int, SpineCoding]:
    coding: SpineCoding = NRLF_TO_SPINE_4XX_ERROR.get(
        exception.__class__, SpineCoding.SERVICE_ERROR
    )
    http_status: HTTPStatus = HTTP_STATUS_CODE_MAPPING[coding]
    return http_status, coding


def _operation_outcome(
    id: str,
    issue_type: IssueType,
    coding: SpineCoding,
    severity: IssueSeverity,
    diagnostics: str,
) -> dict:
    issue_details = CodeableConcept(coding=[coding.value])
    issue = [
        OperationOutcomeIssue(
            code=issue_type.value,
            severity=severity.value,
            diagnostics=diagnostics,
            details=issue_details,
        )
    ]
    return OperationOutcome(
        resourceType=OperationOutcome.__name__, id=id, meta=META, issue=issue
    ).dict(exclude_none=True)


def get_error_message(exception: Exception) -> str:
    return (
        _format_validation_error_message(exception=exception)
        if type(exception) is ValidationError
        else str(
            exception
        )  ### TODO: better error message, e.g. error type in the message?
    )


def _format_validation_error_message(exception: ValidationError) -> str:
    errors = json_loads(exception.json())
    first_error = errors[0]
    model_name = (
        exception.model.public_alias()
        if exception.model.__dict__.get("public_alias")
        else exception.model.__name__
    )
    error_msg_prefix = f"{model_name} validation failure"
    first_bad_property = f"Invalid {first_error['loc'][0]}"
    message_components = [error_msg_prefix, first_bad_property]
    if first_error["type"] == "value_error":
        message_components.append(first_error["msg"])
    return " - ".join(message_components)


def operation_outcome_ok(transaction_id: str, coding: NrlfCoding) -> dict:
    _coding: Coding = coding.value
    operation_outcome = _operation_outcome(
        id=transaction_id,
        coding=coding,
        diagnostics=_coding.display,
        issue_type=IssueType.INFORMATIONAL,
        severity=IssueSeverity.INFORMATION,
    )
    return operation_outcome


def operation_outcome_not_ok(
    transaction_id: str, exception: Exception
) -> tuple[int, dict]:
    status_code, coding = _get_error_from_exception(exception=exception)
    diagnostics = get_error_message(exception=exception)
    operation_outcome = _operation_outcome(
        id=transaction_id,
        coding=coding,
        diagnostics=diagnostics,
        issue_type=IssueType.PROCESSING,
        severity=IssueSeverity.ERROR,
    )
    return status_code, operation_outcome
