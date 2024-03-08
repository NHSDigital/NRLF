from lambda_utils.logging import add_log_fields, log_action
from pydantic import BaseModel, ValidationError

from nrlf.core_pipeline.model import DocumentPointer
from nrlf.core_pipeline.validators import json_loads
from nrlf.log_references import LogReference
from nrlf.producer.fhir.r4.model import DocumentReference


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
    log_reference=LogReference.SEEDVALIDATE001,
    log_fields=["item"],
    log_result=True,
)
def _is_item_valid(item: BaseModel):
    try:
        if type(item) == DocumentPointer:
            add_log_fields(
                pointer_id=item.id,
                pointer_producer_id=item.producer_id,
                pointer_type=item.type,
                pointer_version=item.version,
                pointer_source=item.source,
            )
            DocumentReference(**json_loads(item.document.__root__))
            return True
        else:
            return True
    except ValidationError:
        return False
