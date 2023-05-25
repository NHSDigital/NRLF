from enum import Enum

from lambda_utils.logging import log_action
from pydantic import BaseModel, ValidationError

from nrlf.core.model import DocumentPointer
from nrlf.core.validators import json_loads
from nrlf.producer.fhir.r4.model import DocumentReference


class LogReference(Enum):
    SEEDVALIDATE001 = "Validating item"


def validate_items(items: list[BaseModel], logger=None):
    valid_items = list()

    for item in items:
        try:
            if _is_item_valid(item, logger=logger):
                valid_items.append(item)
        except ValidationError:
            continue

    return valid_items


@log_action(
    log_reference=LogReference.SEEDVALIDATE001, log_fields=["item"], log_result=True
)
def _is_item_valid(item: BaseModel):
    try:
        if type(item) == DocumentPointer:
            DocumentReference(**json_loads(item.document.__root__))
            return True
        else:
            return True
    except ValidationError:
        return False
