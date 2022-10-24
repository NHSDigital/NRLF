from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, validator

from .constants import LEGACY_SYSTEM, MIME_TYPES, UPDATE_DATE_FORMAT


def validate_update_date(update_date: str):
    return datetime.strptime(update_date, UPDATE_DATE_FORMAT)


class Attachment(BaseModel):
    url: HttpUrl
    data: str = None
    language: str = None
    contentType: MIME_TYPES
    creation: str
    hash: str = None


class Coding(BaseModel):
    id: Optional[str] = None
    system: Optional[HttpUrl] = LEGACY_SYSTEM
    code: str
    display: str


class Metadata(BaseModel):
    versionId: str
    profile: list[str]
    lastUpdated: datetime

    @validator("lastUpdated", pre=True)
    def validate_last_updated(value):
        return validate_update_date(update_date=value)


class Period(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class PracticeSetting(BaseModel):
    practiceSettingCoding: list[Coding]
    practiceSettingText: Optional[str] = None


class Context(BaseModel):
    period: Optional[Period]
    practiceSetting: PracticeSetting


class ValueCodeableConcept(BaseModel):
    coding: list[Coding]


class Extension(BaseModel):
    valueCodeableConcept: ValueCodeableConcept
    url: str


class ContentItem(BaseModel):
    attachment: Attachment
    format: Coding
    extension: list[Extension]


class CodeableConcept(BaseModel):
    coding: list[Coding]
    text: Optional[str] = None


class LogicalIdentifier(BaseModel):
    logicalId: str


class Identifier(BaseModel):
    system: str = None
    value: str = None


class Reference(BaseModel):
    reference: Optional[HttpUrl] = None
    identifier: Optional[Identifier] = None


class DataDocumentType(BaseModel):
    code: str
    display: str


class RelatesTo(BaseModel):
    code: Optional[str] = None
    target: Reference


class LegacyDocumentPointer(BaseModel):
    status: Literal["current"]
    type: Coding
    class_: CodeableConcept = Field(alias="class")
    indexed: datetime
    author: Reference
    custodian: Reference
    relatesTo: Optional[RelatesTo]
    content: list[ContentItem]
    context: Context
    logicalIdentifier: LogicalIdentifier
    # Used to update DocumentPointer.[dates]
    lastModified: datetime
    # Not used in transformation to DocumentReference
    masterIdentifier: Optional[Identifier]
    created: Optional[datetime]
    attachment: Attachment
    format: Coding
    meta: Metadata
    stability: CodeableConcept
    removed: Annotated[
        Literal[False],
        Field(description="Soft-deleting functionality is being removed in 'old'"),
    ]

    @validator("lastModified", pre=True)
    def validate_last_updated(value):
        return validate_update_date(update_date=value)
