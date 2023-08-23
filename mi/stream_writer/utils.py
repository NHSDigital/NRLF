import hashlib

from mi.stream_writer.constants import (
    UNDERSCORE_SUB,
    UPPER_LOWER_CASE_BOUNDARY_RE,
    UPPER_TO_LOWER_WITH_UNDERSCORE_RE,
    DocumentPointerPkPrefix,
)


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
