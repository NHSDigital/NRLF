from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.constants import REQUIRED_CREATE_FIELDS
from nrlf.core.errors import ParseError
from nrlf.core.logger import logger
from nrlf.core.types import DocumentReference, OperationOutcomeIssue, RequestQueryType
from nrlf.producer.fhir.r4 import model as producer_model


def validate_type_system(
    type_: Optional[RequestQueryType], pointer_types: List[str]
) -> bool:
    """
    Validates if the given type system is present in the list of pointer types.
    """
    if not type_:
        return True

    type_code = type_.__root__.split("|", 1)[1]
    pointer_type_codes = [
        pointer_type.split("|", 1)[1] for pointer_type in pointer_types
    ]

    return type_code in pointer_type_codes


@dataclass
class ValidationResult:
    resource: DocumentReference
    issues: List[OperationOutcomeIssue]

    def reset(self):
        self.__init__(resource=producer_model.DocumentReference.construct(), issues=[])

    def add_error(
        self,
        issue_code: str,
        error_code: Optional[str] = None,
        diagnostics: Optional[str] = None,
        field: Optional[str] = None,
    ):
        details = None
        if error_code is not None:
            details = SpineErrorConcept.from_code(error_code)

        issue = producer_model.OperationOutcomeIssue(
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
        return not any(issue.severity in {"error", "fatal"} for issue in self.issues)


class StopValidationError(Exception):
    pass


class DocumentReferenceValidator:
    """
    A class to validate document references
    """

    def __init__(self):
        self.result = ValidationResult(
            resource=producer_model.DocumentReference.construct(), issues=[]
        )

    @classmethod
    def parse(cls, data: Dict[str, Any]):
        try:
            result = producer_model.DocumentReference.parse_obj(data)
            logger.debug("Parsed DocumentReference resource", result=result)
            return result

        except ValidationError as exc:
            logger.error(
                "Failed to parse DocumentReference resource",
                data=data,
                validation_error=exc,
            )
            raise ParseError.from_validation_error(
                exc,
                details=SpineErrorConcept.from_code("INVALID_RESOURCE"),
                msg="Failed to parse DocumentReference resource",
            ) from None

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

        except StopValidationError:
            logger.info("Validation stopped due to errors", result=self.result)

        return self.result

    def _validate_required_fields(self, model: DocumentReference):
        """
        Validate the required fields
        """
        logger.debug("Validating required fields")

        for field in REQUIRED_CREATE_FIELDS:
            if not getattr(model, field, None):
                self.result.add_error(
                    issue_code="required",
                    error_code="INVALID_RESOURCE",
                    diagnostics=f"The required field '{field}' is missing",
                    field=field,
                )

        logger.debug(self.result.is_valid)
        if not self.result.is_valid:
            raise StopValidationError()

    def _validate_no_extra_fields(self, model: DocumentReference, data: Dict[str, Any]):
        """
        Validate that there are no extra fields
        """
        logger.debug("Validating no extra fields")

        if data != model.dict(exclude_none=True):
            self.result.add_error(
                issue_code="invalid",
                error_code="INVALID_RESOURCE",
                diagnostics="The resource contains extra fields",
            )

    def _validate_identifiers(self, model: DocumentReference):
        """ """
        logger.debug("Validating identifiers")

        if not (custodian_identifier := getattr(model.custodian, "identifier", None)):
            self.result.add_error(
                issue_code="required",
                error_code="INVALID_RESOURCE",
                diagnostics="Custodian must have an identifier",
                field="custodian.identifier",
            )
            raise StopValidationError()

        if not (subject_identifier := getattr(model.subject, "identifier", None)):
            self.result.add_error(
                issue_code="required",
                error_code="INVALID_RESOURCE",
                diagnostics="Subject must have an identifier",
                field="subject.identifier",
            )
            raise StopValidationError()

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
                diagnostics=(
                    "Provided subject identifier system is not the NHS number system "
                    "(expected 'https://fhir.nhs.uk/Id/nhs-number')"
                ),
                field="subject.identifier.system",
            )

    def _validate_relates_to(self, model: DocumentReference):
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
