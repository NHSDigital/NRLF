from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from pydantic import ValidationError

from nrlf.core_nonpipeline.logger import logger
from nrlf.producer.fhir.r4.model import CodeableConcept, Coding
from nrlf.producer.fhir.r4.model import DocumentReference as ProducerDocumentReference
from nrlf.producer.fhir.r4.model import OperationOutcomeIssue


class ParseError(Exception):
    data: Dict[str, Any]
    issues: List[OperationOutcomeIssue]

    def __init__(self, data: Dict[str, Any], issues: List[OperationOutcomeIssue]):
        self.data = data
        self.issues = issues

    @classmethod
    def from_validation_error(cls, exc: ValidationError, data: Dict[str, Any]):
        issues = []

        for error in exc.errors():
            issues.append(
                OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=CodeableConcept(
                        coding=[
                            Coding(
                                system="https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                                code="INVALID_RESOURCE",
                                display="Invalid validation of resource",
                            )
                        ],
                        text=error["msg"],
                    ),
                    diagnostics=f"{error['loc'][0]}: {error['msg']}",
                    expression=[str(error["loc"][0])],  # type: ignore
                )
            )

        return cls(data, issues)


class StopValidation(Exception):
    pass


IssueCode = Literal["invalid", "structure", "required", "value"]
ErrorCode = Literal[
    "BAD_REQUEST",
    "CONFLICTING_VALUES",
    "DUPLICATE_REJECTED",
    "FHIR_CONSTRAINT_VIOLATION",
    "INTERNAL_SERVER_ERROR",
    "INVALID_CODE_SYSTEM",
    "INVALID_CODE_VALUE",
    "INVALID_ELEMENT",
    "INVALID_IDENTIFIER_SYSTEM",
    "INVALID_IDENTIFIER_VALUE",
    "INVALID_NHS_NUMBER",
    "INVALID_PARAMETER",
    "INVALID_REQUEST_MESSAGE",
    "INVALID_REQUEST_TYPE",
    "INVALID_RESOURCE",
    "INVALID_VALUE",
    "MESSAGE_NOT_WELL_FORMED",
    "INVALID_OR_MISSING_HEADER",
    "NOT_IMPLEMENTED",
    "NO_RECORD_FOUND",
    "ORGANISATION_NOT_FOUND",
    "PRACTITIONER_NOT_FOUND",
    "PRECONDITION_FAILED",
    "REFERENCE_NOT_FOUND",
    "RESOURCE_CREATED",
    "RESOURCE_DELETED",
    "RESOURCE_UPDATED",
]


@dataclass
class ValidationResult:
    resource: ProducerDocumentReference
    issues: List[OperationOutcomeIssue]

    def reset(self):
        self.__init__(resource=ProducerDocumentReference.construct(), issues=[])

    def add_error(
        self,
        issue_code: IssueCode,
        error_code: Optional[ErrorCode] = None,
        diagnostics: Optional[str] = None,
        field: Optional[str] = None,
    ):
        details = None
        if error_code is not None:
            details = CodeableConcept(
                coding=[
                    Coding(
                        system="https://fhir.nhs.uk/ValueSet/Spine-ErrorOrWarningCode-1",
                        code=error_code,
                    )
                ]
            )

        issue = OperationOutcomeIssue(
            severity="error",
            code=issue_code,
            details=details,
            diagnostics=diagnostics,
            expression=[field] if field else None,  # type: ignore
        )

        logger.info("Adding validation issue", issue=issue.dict(exclude_none=True))
        self.issues.append(issue)

    @property
    def is_valid(self):
        return not any([issue.severity in {"error", "fatal"} for issue in self.issues])


class DocumentReferenceValidator:
    """
    A class to validate document references
    """

    def __init__(self):
        self.result = ValidationResult(
            resource=ProducerDocumentReference.construct(), issues=[]
        )

    @classmethod
    def parse(cls, data: Dict[str, Any]):
        try:
            result = ProducerDocumentReference.parse_obj(data)
            logger.debug("Parsed DocumentReference resource", result=result)
            return result

        except ValidationError as exc:
            logger.exception(
                "Failed to parse DocumentReference resource",
                data=data,
                validation_error=exc,
            )
            raise ParseError.from_validation_error(exc, data)

    def validate(self, data: Dict[str, Any]):
        """
        Validate the document reference
        """
        logger.info("Performing validation on DocumentReference resource", data=data)
        resource = self.parse(data)
        self.result = ValidationResult(resource=resource, issues=[])

        try:
            self._validate_required_fields(resource)
            self._validate_no_extra_fields(resource, data)
            self._validate_identifiers(resource)
            self._validate_relates_to(resource)

        except StopValidation:
            logger.info("Validation stopped due to errors", result=self.result)

        return self.result

    def _validate_required_fields(self, model: ProducerDocumentReference):
        """
        Validate the required fields
        """
        logger.debug("Validating required fields")

        required_fields = ["custodian", "id", "type", "status", "subject"]

        for field in required_fields:
            if not getattr(model, field, None):
                self.result.add_error(
                    issue_code="required",
                    error_code="INVALID_RESOURCE",
                    diagnostics=f"The required field {field} is missing",
                    field=field,
                )

        logger.debug(self.result.is_valid)
        if not self.result.is_valid:
            raise StopValidation()

    def _validate_no_extra_fields(
        self, model: ProducerDocumentReference, data: Dict[str, Any]
    ):
        """
        Validate that there are no extra fields
        """
        logger.debug("Validating no extra fields")

        if data != model.dict(exclude_none=True):
            self.result.add_error(
                issue_code="invalid",
                error_code="INVALID_RESOURCE",
                diagnostics="Input FHIR JSON has additional non-FHIR fields.",
            )

    def _validate_identifiers(self, model: ProducerDocumentReference):
        """ """
        logger.debug("Validating identifiers")

        if not (custodian_identifier := getattr(model.custodian, "identifier", None)):
            self.result.add_error(
                issue_code="required",
                error_code="INVALID_RESOURCE",
                diagnostics="Custodian must have an identifier",
                field="custodian.identifier",
            )
            raise StopValidation()

        if not (subject_identifier := getattr(model.subject, "identifier", None)):
            self.result.add_error(
                issue_code="required",
                error_code="INVALID_RESOURCE",
                diagnostics="Subject must have an identifier",
                field="subject.identifier",
            )
            raise StopValidation()

        if (
            custodian_identifier.system
            != "https://fhir.nhs.uk/Id/ods-organization-code"
        ):
            self.result.add_error(
                issue_code="invalid",
                error_code="INVALID_IDENTIFIER_SYSTEM",
                diagnostics="Provided custodian identifier system is not the ODS system (expected: 'https://fhir.nhs.uk/Id/ods-organization-code')",
                field="custodian.identifier.system",
            )

        if subject_identifier.system != "https://fhir.nhs.uk/Id/nhs-number":
            self.result.add_error(
                issue_code="invalid",
                error_code="INVALID_IDENTIFIER_SYSTEM",
                diagnostics="Provided subject identifier system is not the NHS number system (expected 'https://fhir.nhs.uk/Id/nhs-number')",
                field="subject.identifier.system",
            )

    def _validate_relates_to(self, model: ProducerDocumentReference):
        """"""
        if not model.relatesTo:
            logger.debug(
                "Skipping relatesTo validation as there are no relatesTo fields"
            )
            return

        logger.debug("Validating relatesTo")

        for index, relates_to in enumerate(model.relatesTo):
            if relates_to.code not in [
                "replaces",
                "transforms",
                "signs",
                "appends",
                "incorporates",
                "summarizes",
            ]:
                self.result.add_error(
                    issue_code="value",
                    error_code="INVALID_CODE_VALUE",
                    diagnostics=f"Invalid relatesTo code: {relates_to.code}",
                    field=f"relatesTo[{index}].code",
                )
                continue

            if relates_to.code == "replaces" and not (
                relates_to.target.identifier and relates_to.target.identifier.value
            ):
                self.result.add_error(
                    issue_code="required",
                    error_code="INVALID_IDENTIFIER_VALUE",
                    diagnostics="relatesTo code 'replaces' must have a target identifier",
                    field=f"relatesTo[{index}].target.identifier.value",
                )
                continue
