import hashlib

import pytest

from mi.stream_writer.constants import (
    UNDERSCORE_SUB,
    UPPER_LOWER_CASE_BOUNDARY_RE,
    UPPER_TO_LOWER_WITH_UNDERSCORE_RE,
    DocumentPointerPkPrefix,
)
from mi.stream_writer.model import GoodResponse
from nrlf.core.validators import json_loads

RESOURCE_PREFIX = "nhsd-nrlf"
LAMBDA_NAME = RESOURCE_PREFIX + "--{workspace}--mi--stream_writer"


def to_snake_case(camel_case: str):
    with_underscores = UPPER_LOWER_CASE_BOUNDARY_RE.sub(UNDERSCORE_SUB, camel_case)
    snake_case = UPPER_TO_LOWER_WITH_UNDERSCORE_RE.sub(UNDERSCORE_SUB, with_underscores)
    return snake_case.lower()


def hash_nhs_number(nhs_number: str):
    hash = hashlib.new("sha256")
    hash.update(nhs_number.encode())
    return hash.hexdigest()


def is_document_pointer(pk: str, **_other_keys):
    return pk.startswith(DocumentPointerPkPrefix)

def invoke_stream_writer(session, workspace: str, event: dict) -> GoodResponse:
    client = session.client("lambda")
    function_name = get_lambda_name(workspace=workspace)
    result = client.invoke(FunctionName=function_name, Payload=json.dumps(event))
    response_payload = result["Payload"].read().decode("utf-8")
    response: dict = json_loads(response_payload)
    if response.get("error") or response.get("errorMessage"):
        pytest.fail(f"There was an error with the lambda:\n {response_payload}")
    return GoodResponse(**response)


def get_lambda_name(workspace: str) -> str:
    return LAMBDA_NAME.format(workspace=workspace)
