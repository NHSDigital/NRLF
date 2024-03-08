from typing import Dict, List, Optional

from nrlf.core_nonpipeline.logger import logger
from nrlf.producer.fhir.r4.model import OperationOutcome, OperationOutcomeIssue


class OperationOutcomeResponse(Exception):
    def __init__(
        self,
        status_code: Optional[str] = None,
        issues: Optional[List[OperationOutcomeIssue]] = None,
    ):
        self.status_code = status_code or "400"
        self.issues = issues or []

    @property
    def response(self) -> Dict[str, str]:
        resource = OperationOutcome(
            resourceType="OperationOutcome",
            id=logger.get_correlation_id(),
            issue=self.issues,
        )

        return {
            "statusCode": self.status_code,
            "body": resource.json(exclude_none=True, indent=2),
        }


class DatabaseError(Exception):
    pass


class DuplicateIDError(Exception):
    pass
