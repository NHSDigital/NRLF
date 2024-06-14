from dataclasses import dataclass
from re import match
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.constants import CATEGORIES, REQUIRED_CREATE_FIELDS
from nrlf.core.errors import ParseError
from nrlf.core.logger import LogReference, logger
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

    type_system = type_.__root__.split("|", 1)[0]
    pointer_type_systems = [
        pointer_type.split("|", 1)[0] for pointer_type in pointer_types
    ]

    return type_system in pointer_type_systems


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

        logger.log(LogReference.VALIDATOR002, issue=issue.dict(exclude_none=True))
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

    MODEL = producer_model.DocumentReference

    def __init__(self):
        self.result = ValidationResult(resource=self.MODEL.construct(), issues=[])

    @classmethod
    def parse(cls, data: Dict[str, Any]):
        try:
            logger.log(LogReference.PARSE000, data=data, model=cls.MODEL.__name__)
            result = cls.MODEL.parse_obj(data)
            logger.log(LogReference.PARSE001, model=cls.MODEL.__name__)
            logger.log(LogReference.PARSE001a, result=result)
            return result

        except ValidationError as exc:
            logger.log(
                LogReference.PARSE002,
                model=cls.MODEL.__name__,
                data=data,
                validation_error=str(exc),
            )
            raise ParseError.from_validation_error(
                exc,
                details=SpineErrorConcept.from_code("INVALID_RESOURCE"),
                msg="Failed to parse DocumentReference resource",
            ) from None

    def validate(self, data: Dict[str, Any] | DocumentReference):
        """
        Validate the document reference
        """
        logger.log(LogReference.VALIDATOR000, resource_type="DocumentReference")
        resource = self.parse(data) if isinstance(data, dict) else data

        self.result = ValidationResult(resource=resource, issues=[])

        try:
            self._validate_required_fields(resource)
            self._validate_no_extra_fields(resource, data)
            self._validate_identifiers(resource)
            self._validate_relates_to(resource)
            self._validate_ssp_asid(resource)
            self._validate_category(resource)
            if resource.content[0].extension:
                self._validate_content_extension(resource)

        except StopValidationError:
            logger.log(LogReference.VALIDATOR003)

        logger.log(
            LogReference.VALIDATOR999,
            is_valid=self.result.is_valid,
            issue_count=len(self.result.issues),
        )
        return self.result

    def _validate_required_fields(self, model: DocumentReference):
        """
        Validate the required fields
        """
        logger.log(
            LogReference.VALIDATOR001,
            step="required_fields",
            required_fields=REQUIRED_CREATE_FIELDS,
        )

        for field in REQUIRED_CREATE_FIELDS:
            if not getattr(model, field, None):
                self.result.add_error(
                    issue_code="required",
                    error_code="INVALID_RESOURCE",
                    diagnostics=f"The required field '{field}' is missing",
                    field=field,
                )

        if not self.result.is_valid:
            raise StopValidationError()

    def _validate_no_extra_fields(
        self, resource: DocumentReference, data: Dict[str, Any] | DocumentReference
    ):
        """
        Validate that there are no extra fields
        """
        logger.log(LogReference.VALIDATOR001, step="no_extra_fields")
        has_extra_fields = False

        if isinstance(data, DocumentReference):
            has_extra_fields = (
                len(set(resource.__dict__) - set(resource.__fields__)) > 0
            )
        else:
            has_extra_fields = data != resource.dict(exclude_none=True)

        if has_extra_fields:
            self.result.add_error(
                issue_code="invalid",
                error_code="INVALID_RESOURCE",
                diagnostics="The resource contains extra fields",
            )

    def _validate_identifiers(self, model: DocumentReference):
        """ """
        logger.log(LogReference.VALIDATOR001, step="identifiers")

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
            logger.log(
                LogReference.VALIDATOR001, step="relates_to", reason="no_relates_to"
            )
            return

        logger.log(LogReference.VALIDATOR001, step="relates_to")

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

    def _validate_asid(self, asid_references: list):
        """
        Validate that the ASID provided in the document is valid
        """
        logger.log(LogReference.VALIDATOR001, step="ssp_asid")

        if len(asid_references) > 1:
            self.result.add_error(
                issue_code="invalid",
                error_code="INVALID_RESOURCE",
                diagnostics="Multiple ASID identifiers provided. Only a single valid ASID identifier can be provided in the context.related.",
                field="context.related",
            )
            return

        idx, asid_reference = asid_references[0]
        asid_value = getattr(asid_reference.identifier, "value", "")
        if not match(r"^\d{12}$", asid_value):
            self.result.add_error(
                issue_code="value",
                error_code="INVALID_IDENTIFIER_VALUE",
                diagnostics=f"Invalid ASID value '{asid_value}'. A single ASID consisting of 12 digits can be provided in the context.related field.",
                field=f"context.related[{idx}].identifier.value",
            )
            return

    def _validate_ssp_asid(self, model: DocumentReference):
        """
        Validate that the document contains a valid ASID in the context.related field when the content contains an SSP URL
        """

        ssp_content = any(
            [
                content
                for content in model.content
                if content.attachment.url.startswith("ssp://")
            ]
        )

        logger.log(LogReference.VALIDATOR001, step="ssp_content_and_asid_exists")

        does_related_exist = getattr(model.context, "related", None)
        does_asid_exist = False
        if does_related_exist:
            asid_references = [
                (idx, related)
                for idx, related in enumerate(getattr(model.context, "related", []))
                if related.identifier.system == "https://fhir.nhs.uk/Id/nhsSpineASID"
            ]
            if len(asid_references) > 0:
                does_asid_exist = True
                self._validate_asid(asid_references)

        if not does_asid_exist and not ssp_content:
            logger.log(
                LogReference.VALIDATOR001a, step="ssp_asid", reason="no_ssp_content"
            )
            return

        if ssp_content and not does_related_exist:
            self.result.add_error(
                issue_code="required",
                error_code="INVALID_RESOURCE",
                diagnostics="Missing context.related. It must be provided and contain a single valid ASID identifier when content contains an SSP URL",
                field="context.related",
            )
            return

        if ssp_content and does_related_exist and not does_asid_exist:
            self.result.add_error(
                issue_code="required",
                error_code="INVALID_RESOURCE",
                diagnostics="Missing ASID identifier. context.related must contain a single valid ASID identifier when content contains an SSP URL",
                field="context.related",
            )
            return

    def _validate_category(self, model: DocumentReference):
        """
        Validate the category field contains an appropriate coding system, code and display.
        """

        if len(model.category) > 1:
            logger.log(
                LogReference.VALIDATOR001, step="category", reason="category_too_long"
            )
            self.result.add_error(
                issue_code="invalid",
                error_code="INVALID_RESOURCE",
                diagnostics=f"Invalid category length: {len(model.category)} Category must only contain a single value",
                field=f"category",
            )
            return

        logger.log(LogReference.VALIDATOR001, step="category")

        logger.debug("Validating category")

        if len(model.category[0].coding) > 1:
            self.result.add_error(
                issue_code="invalid",
                error_code="INVALID_RESOURCE",
                diagnostics=f"Invalid category coding length: {len(model.category[0].coding)} Category Coding must only contain a single value",
                field=f"category[0].coding",
            )
            return

        coding = model.category[0].coding[0]
        if coding.system != "http://snomed.info/sct":
            self.result.add_error(
                issue_code="value",
                error_code="INVALID_RESOURCE",
                diagnostics=f"Invalid category system: {coding.system} Category system must be 'http://snomed.info/sct'",
                field=f"category[0].coding[{0}].system",
            )
            return

        if coding.code not in CATEGORIES.keys():
            self.result.add_error(
                issue_code="value",
                error_code="INVALID_RESOURCE",
                diagnostics=f"Invalid category code: {coding.code} Category must be a member of the England-NRLRecordCategory value set (https://fhir.nhs.uk/England/CodeSystem/England-NRLRecordCategory)",
                field=f"category[0].coding[{0}].code",
            )
            return

        if coding.display != CATEGORIES.get(coding.code):
            self.result.add_error(
                issue_code="value",
                error_code="INVALID_RESOURCE",
                diagnostics=f"category code '{coding.code}' must have a display value of '{CATEGORIES.get(coding.code)}'",
                field=f"category[0].coding[{0}].display",
            )

    def _validate_content_extension(self, model: DocumentReference):
        """
        Validate the content.extension field contains an appropriate coding.
        """
        logger.log(LogReference.VALIDATOR001, step="content extension")

        logger.debug("Validating extension")
        for i, content in enumerate(model.content):
            if len(content.extension) > 1:
                logger.log(
                    LogReference.VALIDATOR001,
                    step=f"content[{i}].extension",
                    reason="extension_too_long",
                )
                self.result.add_error(
                    issue_code="invalid",
                    error_code="INVALID_RESOURCE",
                    diagnostics=f"Invalid content extension length: {len(content.extension)} Extension must only contain a single value",
                    field=f"content[{i}].extension",
                )
                return

            if len(content.extension[0].valueCodeableConcept.coding) < 1:
                logger.log(
                    LogReference.VALIDATOR001,
                    step=f"content[{i}].extension.valueCodeableConcept.coding",
                    reason="extension_coding_does_not_exist",
                )
                self.result.add_error(
                    issue_code="required",
                    error_code="INVALID_RESOURCE",
                    diagnostics=f"Missing content[{i}].extension[0].valueCodeableConcept.coding, extension must have at least one coding.",
                    field=f"content[{i}].extension.valueCodeableConcept.coding",
                )
                return

            if (
                content.extension[0].valueCodeableConcept.coding[0].system
                != "https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability"
            ):
                logger.log(
                    LogReference.VALIDATOR001,
                    step=f"content[{i}].extension.valueCodeableConcept.coding[0].system",
                    reason="extension_coding_system_invalid",
                )
                self.result.add_error(
                    issue_code="value",
                    error_code="INVALID_RESOURCE",
                    diagnostics=f"Invalid content extension system: {content.extension[0].valueCodeableConcept.coding[0].system} Extension system must be 'https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability'",
                    field=f"content[{i}].extension[0].valueCodeableConcept.coding[0].system",
                )
                return

            if content.extension[0].valueCodeableConcept.coding[0].code not in [
                "static",
                "dynamic",
            ]:
                logger.log(
                    LogReference.VALIDATOR001,
                    step=f"content[{i}].extension.valueCodeableConcept.coding[0].code",
                    reason="extension_coding_code_invalid",
                )
                self.result.add_error(
                    issue_code="value",
                    error_code="INVALID_RESOURCE",
                    diagnostics=f"Invalid content extension code: {content.extension[0].valueCodeableConcept.coding[0].code} Extension code must be 'static' or 'dynamic'",
                    field=f"content[{i}].extension[0].valueCodeableConcept.coding[0].code",
                )
                return

            if (
                content.extension[0].valueCodeableConcept.coding[0].code
                != content.extension[0].valueCodeableConcept.coding[0].display.lower()
            ):
                logger.log(
                    LogReference.VALIDATOR001,
                    step=f"content[{i}].extension.valueCodeableConcept.coding[0].display",
                    reason="extension_coding_display_invalid",
                )
                self.result.add_error(
                    issue_code="value",
                    error_code="INVALID_RESOURCE",
                    diagnostics=f"Invalid content extension display: {content.extension[0].valueCodeableConcept.coding[0].display} Extension display must be the same as code either 'static' or 'dynamic'",
                    field=f"content[{i}].extension[0].valueCodeableConcept.coding[0].display",
                )
                return

            if (
                content.extension[0].url
                != "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-ContentStability"
            ):
                logger.log(
                    LogReference.VALIDATOR001,
                    step=f"content[{i}].extension.url",
                    reason="extension_url_invalid",
                )
                self.result.add_error(
                    issue_code="value",
                    error_code="INVALID_RESOURCE",
                    diagnostics=f"Invalid content extension url: {content.extension[0].url} Extension url must be 'https://fhir.nhs.uk/England/StructureDefinition/Extension-England-ContentStability'",
                    field=f"content[{i}].extension[0].url",
                )
                return
