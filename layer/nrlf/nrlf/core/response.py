from typing import List

from pydantic import BaseModel, Field

from nrlf.core.codes import SpineErrorConcept
from nrlf.core.types import Bundle, OperationOutcomeIssue
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
    def from_bundle(
        cls, bundle: Bundle, statusCode: str = "200", **kwargs
    ) -> "Response":
        return cls(
            statusCode=statusCode,
            body=bundle.json(indent=2, exclude_none=True, exclude_defaults=True),
            **kwargs,
        )

    @classmethod
    def from_resource(
        cls, resource: BaseModel, statusCode: str = "200", **kwargs
    ) -> "Response":
        return cls(
            statusCode=statusCode,
            body=resource.json(indent=2, exclude_none=True),
            **kwargs,
        )

    @classmethod
    def from_issues(cls, issues: List[OperationOutcomeIssue], **kwargs) -> "Response":
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
