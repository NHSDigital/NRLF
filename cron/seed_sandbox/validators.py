import json

from nrlf.core.model import DocumentPointer
from nrlf.producer.fhir.r4.model import DocumentReference
from pydantic import BaseModel, ValidationError


def validate_items(items: list[BaseModel]):
    valid_items = list()

    for item in items:
        try:
            if _is_item_valid(item):
                valid_items.append(item)
        except ValidationError:
            continue

    return valid_items


def _is_item_valid(item: BaseModel):
    try:
        if type(item) == DocumentPointer:
            DocumentReference(**json.loads(item.document.__root__))
            return True
        else:
            return True
    except ValidationError:
        return False
