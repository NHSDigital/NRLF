from copy import deepcopy
from pydantic import BaseModel, Field
from polyfactory.factories.pydantic_factory import ModelFactory
from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime as dt
from mi.stream_writer.index import EVENT_CONFIG

from nrlf.core.model import DocumentPointer


N_SAMPLES = 100_000
PK = "D#{}"

STREAM_EVENT = {
    "eventID": "",
    "eventName": "<<EVENT_NAME>>",
    "eventVersion": "",
    "eventSource": "",
    "awsRegion": "",
    "dynamodb": {
        "ApproximateCreationDateTime": 0,
        "Keys": {},
        "<<IMAGE_TYPE>>": {},
        "SequenceNumber": "0",
        "SizeBytes": 0,
        "StreamViewType": "NEW_AND_OLD_IMAGES",
    },
    "eventSourceARN": "",
}


class DocumentPointerMI(BaseModel):
    type: str = Field(regex=r"^http://snomed.info/sct\|(\d[9])$")
    custodian: str = Field(regex=r"^[A-Z][2][A-Z0-9][3]$")
    custodian_suffix: str = Field(regex=r"^[A-Z][2][A-Z0-9][3]$")
    nhs_number: str = Field(regex=r"^[0-9][10]$")
    created_on: int = Field(
        ge=dt(year=2023, month=6, day=1).toordinal(),
        le=dt(year=2025, month=12, day=31).toordinal(),
    )
    event_name: Literal["INSERT", "REMOVE"]


class Factory(ModelFactory[DocumentPointerMI]):
    __model__ = DocumentPointerMI


def main():
    for pk in map(PK.format, range(N_SAMPLES)):
        doc_ref_mi = Factory.build().dict()
        event_name = doc_ref_mi.pop("event_name")
        image_type = EVENT_CONFIG[event_name].image_type

        basic_document_pointer = {"pk": pk, "sk": pk, **doc_ref_mi}
        stream_event = {**deepcopy(STREAM_EVENT), **{"eventName": event_name}}
        stream_event["dynamodb"]
