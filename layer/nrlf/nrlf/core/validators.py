import json

from nhs_number import is_valid as is_valid_nhs_number
from nrlf.core.constants import VALID_STATUSES
from requests import JSONDecodeError


def _get_id_components(id: str) -> bool:
    producer_id, local_id = id.split("|")
    return producer_id, local_id


def _is_json(document: str) -> bool:
    try:
        json.loads(document)
    except JSONDecodeError:
        return False
    return True


def validate_id(id: str, producer_id: str):
    try:
        producer_id_from_id, _ = _get_id_components(id)
    except ValueError:
        raise ValueError(f"ID is not composite of the form producer_id|local_id: {id}")
    if producer_id_from_id != producer_id:
        raise ValueError(f"{producer_id} != {producer_id_from_id}")


def validate_nhs_number(nhs_number: str):
    if not is_valid_nhs_number(nhs_number):
        raise ValueError(f"Not a valid NHS Number: {nhs_number}")


def validate_status(status: str):
    if status not in VALID_STATUSES:
        raise ValueError(f"Not a status: {status}. Expected one of {VALID_STATUSES}.")


def validate_document(document: str):
    if not _is_json(document):
        raise ValueError(f"Not valid JSON: {document}")
