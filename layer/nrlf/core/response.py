# ruff: noqa: N803, N815

from typing import List

from pydantic.v1 import BaseModel, Field

from nrlf.core.codes import NRLResponseConcept, SpineErrorConcept
from nrlf.core.constants import PRODUCER_URL_PATH
from nrlf.producer.fhir.r4 import model as producer_model


class Response(BaseModel):
    """
    Represents an API Gateway HTTP response.
    """

    statusCode: str
    body: str
    headers: dict = Field(default_factory=dict)
    isBase64Encoded: bool = Field(default=False)

    @classmethod
    def from_resource(
        cls, resource: BaseModel, statusCode: str = "200", **kwargs
    ) -> "Response":
        return cls(
            statusCode=statusCode,
            body=resource.json(indent=2, exclude_none=True, exclude_defaults=True),
            **kwargs,
        )

    @classmethod
    def from_issues(cls, issues: List[BaseModel], **kwargs) -> "Response":
        return cls(
            body=producer_model.OperationOutcome(
                resourceType="OperationOutcome",
                issue=issues,  # type: ignore
            ).json(exclude_none=True, indent=2),
            **kwargs,
        )

    @classmethod
    def from_exception(cls, exc: Exception) -> "Response":
        return cls(
            statusCode="500",
            body=producer_model.OperationOutcome(
                resourceType="OperationOutcome",
                issue=[
                    producer_model.OperationOutcomeIssue(
                        severity="error",
                        code="exception",
                        diagnostics=str(exc),
                        details=SpineErrorConcept.from_code("INTERNAL_SERVER_ERROR"),
                    )
                ],
            ).json(exclude_none=True, indent=2),
        )


class NRLResponse(Response):
    @classmethod
    def RESOURCE_CREATED(cls, resource_id: str):
        return cls.from_issues(
            issues=[
                producer_model.OperationOutcomeIssue(
                    severity="information",
                    code="informational",
                    details=NRLResponseConcept.from_code("RESOURCE_CREATED"),
                    diagnostics="The document has been created",
                )
            ],
            statusCode="201",
            headers={"Location": f"{PRODUCER_URL_PATH}/{resource_id}"},
        )

    @classmethod
    def RESOURCE_SUPERSEDED(cls, resource_id: str):
        return cls.from_issues(
            issues=[
                producer_model.OperationOutcomeIssue(
                    severity="information",
                    code="informational",
                    details=NRLResponseConcept.from_code("RESOURCE_SUPERSEDED"),
                    diagnostics="The document has been superseded by a new version",
                )
            ],
            statusCode="201",
            headers={"Location": f"{PRODUCER_URL_PATH}/{resource_id}"},
        )

    @classmethod
    def RESOURCE_UPDATED(cls):
        return cls.from_issues(
            issues=[
                producer_model.OperationOutcomeIssue(
                    severity="information",
                    code="informational",
                    details=NRLResponseConcept.from_code("RESOURCE_UPDATED"),
                    diagnostics="The DocumentReference has been updated",
                )
            ],
            statusCode="200",
        )

    @classmethod
    def RESOURCE_DELETED(cls):
        return cls.from_issues(
            issues=[
                producer_model.OperationOutcomeIssue(
                    severity="information",
                    code="informational",
                    details=NRLResponseConcept.from_code("RESOURCE_DELETED"),
                    diagnostics="The requested DocumentReference has been deleted",
                )
            ],
            statusCode="200",
        )


class SpineErrorResponse(Response):
    @classmethod
    def NO_RECORD_FOUND(
        cls, diagnostics: str = "The requested resource could not be found"
    ) -> "Response":
        return cls.from_issues(
            issues=[
                producer_model.OperationOutcomeIssue(
                    severity="error",
                    code="not-found",
                    details=SpineErrorConcept.from_code("NO_RECORD_FOUND"),
                    diagnostics=diagnostics,
                )
            ],
            statusCode="404",
        )

    @classmethod
    def ACCESS_DENIED(cls, diagnostics: str = "Access denied") -> "Response":
        return cls.from_issues(
            issues=[
                producer_model.OperationOutcomeIssue(
                    severity="error",
                    code="forbidden",
                    details=SpineErrorConcept.from_code("ACCESS DENIED"),
                    diagnostics=diagnostics,
                )
            ],
            statusCode="403",
        )

    @classmethod
    def INVALID_IDENTIFIER_VALUE(
        cls,
        diagnostics: str = "Invalid identifier value",
        expression: str | None = None,
    ):
        return cls.from_issues(
            issues=[
                producer_model.OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("INVALID_IDENTIFIER_VALUE"),
                    diagnostics=diagnostics,
                    expression=(
                        [producer_model.ExpressionItem(__root__=expression)]
                        if expression
                        else None
                    ),
                )
            ],
            statusCode="400",
        )

    @classmethod
    def INVALID_NHS_NUMBER(
        cls, diagnostics: str = "Invalid NHS number", expression: str | None = None
    ) -> "Response":
        return cls.from_issues(
            issues=[
                producer_model.OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("INVALID_NHS_NUMBER"),
                    diagnostics=diagnostics,
                    expression=(
                        [producer_model.ExpressionItem(__root__=expression)]
                        if expression
                        else None
                    ),
                )
            ],
            statusCode="400",
        )

    @classmethod
    def INVALID_CODE_SYSTEM(
        cls, diagnostics: str = "Invalid code system", expression: str | None = None
    ) -> "Response":
        return cls.from_issues(
            issues=[
                producer_model.OperationOutcomeIssue(
                    severity="error",
                    code="code-invalid",
                    details=SpineErrorConcept.from_code("INVALID_CODE_SYSTEM"),
                    diagnostics=diagnostics,
                    expression=(
                        [producer_model.ExpressionItem(__root__=expression)]
                        if expression
                        else None
                    ),
                )
            ],
            statusCode="400",
        )

    @classmethod
    def BAD_REQUEST(
        cls, diagnostics: str = "Bad request", expression: str | None = None
    ) -> "Response":
        return cls.from_issues(
            issues=[
                producer_model.OperationOutcomeIssue(
                    severity="error",
                    code="invalid",
                    details=SpineErrorConcept.from_code("BAD_REQUEST"),
                    diagnostics=diagnostics,
                    expression=(
                        [producer_model.ExpressionItem(__root__=expression)]
                        if expression
                        else None
                    ),
                )
            ],
            statusCode="400",
        )

    @classmethod
    def AUTHOR_CREDENTIALS_ERROR(
        cls, diagnostics: str, expression: str | None = None
    ) -> "Response":
        return cls.from_issues(
            issues=[
                producer_model.OperationOutcomeIssue(
                    severity="error",
                    code="forbidden",
                    details=SpineErrorConcept.from_code("AUTHOR_CREDENTIALS_ERROR"),
                    diagnostics=diagnostics,
                    expression=(
                        [producer_model.ExpressionItem(__root__=expression)]
                        if expression
                        else None
                    ),
                )
            ],
            statusCode="403",
        )
