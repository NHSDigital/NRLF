import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from nhs_number import is_valid as is_valid_nhs_number
from pydantic import BaseModel, Field, PrivateAttr, root_validator, validator

from nrlf.core.constants import VALID_SOURCES
from nrlf.core.types import DocumentReference


class DBPrefix(str, Enum):
    DocumentPointer = "D"
    Patient = "P"
    CreatedOn = "CO"
    Organisation = "O"
    Contract = "C"
    Version = "V"


KEBAB_CASE_RE = re.compile(r"(?<!^)(?=[A-Z])")


class DynamoDBModel(BaseModel):
    _from_dynamo: bool = PrivateAttr(default=False)

    @classmethod
    def kebab(cls) -> str:
        return KEBAB_CASE_RE.sub("-", cls.__name__).lower()

    @classmethod
    def public_alias(cls) -> str:
        return cls.__name__


class DocumentPointer(DynamoDBModel):
    id: str
    nhs_number: str
    custodian: str
    custodian_suffix: Optional[str] = None
    producer_id: str
    type: str
    source: str
    version: int
    document: str
    created_on: str
    updated_on: Optional[str] = None
    document_id: str = Field(exclude=True)
    schemas: list = Field(default_factory=list)
    _document: Optional[dict] = PrivateAttr()

    def __init__(self, *, _document: Optional[dict] = None, **data):
        super().__init__(**data)
        self._document = _document

    def dict(self, **kwargs) -> dict:
        """
        Override dict() to include partition and sort keys
        """
        default_dict = super().dict(**kwargs)
        return {
            **default_dict,
            "pk": self.pk,
            "sk": self.sk,
            "pk_1": self.pk_1,
            "sk_1": self.sk_1,
            "pk_2": self.pk_2,
            "sk_2": self.sk_2,
        }

    @classmethod
    def from_document_reference(
        cls, resource: DocumentReference, created_on: Optional[str] = None
    ) -> "DocumentPointer":
        if not (
            resource.subject
            and resource.subject.identifier
            and resource.custodian
            and resource.custodian.identifier
            and resource.type
            and resource.type.coding
        ):
            raise ValueError(
                "DocumentReference must have a subject, custodian and type"
            )

        coding = resource.type.coding[0]
        pointer_type = f"{coding.system}|{coding.code}"

        return cls(
            id=resource.id,
            nhs_number=resource.subject.identifier.value,
            custodian=resource.custodian.identifier.value,
            type=pointer_type,
            source="NRLF",
            version=1,
            document=resource.json(exclude_none=True),
            created_on=created_on
            or datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds") + "Z",
            _document=resource.dict(exclude_none=True),
        )

    @root_validator(pre=True)
    @classmethod
    def extract_custodian_suffix(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the custodian suffix if it is not provided and the custodian
        is in the format <custodian>.<custodian_suffix>
        """

        custodian = values.get("custodian")
        custodian_suffix = values.get("custodian_suffix")

        if custodian and not custodian_suffix:
            split_custodian = custodian.split(".")

            if len(split_custodian) == 2:
                custodian, custodian_suffix = split_custodian
                values["custodian"] = custodian

        if custodian_suffix is not None:
            values["custodian_suffix"] = custodian_suffix

        return values

    @root_validator(pre=True)
    @classmethod
    def inject_producer_id(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject the producer_id into the DocumentPointer if it is not provided
        """
        _id: str = values["id"]
        producer_id = values.get("producer_id")

        if values.get("_from_dynamo"):
            producer_id = None

        if producer_id is not None:
            raise ValueError(
                "producer_id should not be passed to DocumentPointer; "
                "it will be extracted from id."
            )

        producer_id, document_id = _id.split("-", maxsplit=1)

        values["producer_id"] = producer_id
        values["document_id"] = document_id
        return values

    # @root_validator(pre=True)
    # def coerce_document_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Coerce the DocumentReference.type to a string if provided as a CodeableConcept
    #     """
    #     if values.get("_from_dynamo"):
    #         return values

    #     document_type = values.get("type")
    #     assert isinstance(document_type, CodeableConcept), "type must be a CodeableConcept"

    #     if not document_type.coding or len(document_type.coding) != 1:
    #         raise ValueError("DocumentReference.type.coding must have exactly one item")

    #     coding = document_type.coding[0]
    #     values["type"] = f"{coding.system}|{coding.code}"

    #     return values

    # @root_validator(pre=True)
    # def coerce_document(cls, values: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Coerce the DocumentReference.document to a dict if provided as a string
    #     """
    #     if not values.get("_from_dynamo"):
    #         return values

    #     document = values.get("document")
    #     if isinstance(document, str):
    #         values["document"] = json.loads(document)

    #     return values

    @validator("id")
    @classmethod
    def validate_id(cls, id_: str) -> str:
        """
        Validate the id of the DocumentPointer
        The id should be in the format <producer_id>-<document_id>
        """
        if not re.match(r"^[A-Za-z0-9]+-[A-Za-z0-9\-_]+$", id_):
            raise ValueError("id must be in the format <producer_id>-<document_id>")

        return id_

    @validator("producer_id")
    @classmethod
    def validate_producer_id(cls, producer_id: str, values: Dict[str, Any]) -> str:
        id_ = values.get("id")
        custodian = values.get("custodian_id")
        custodian_suffix = values.get("custodian_suffix")

        if not all([id_, custodian, custodian_suffix]):
            return producer_id

        if custodian_suffix:
            if producer_id.split(".") != (custodian, custodian_suffix):
                # TODO: Original Error MalformedProducerId
                raise ValueError(
                    f"Producer ID {producer_id} (extracted from '{id_}') is not correctly formed. "
                    "It is expected to be composed in the form '<custodian_id>.<custodian_suffix>'"
                )

        elif producer_id != custodian:
            raise ValueError(
                f"Producer ID {producer_id} (extracted from '{id_}')"
                " does not match the Custodian ID."
            )

        return producer_id

    @validator("type")
    @classmethod
    def validate_type(cls, type: str) -> str:
        """
        Validate the type of the DocumentPointer
        The type should be in the format <system>|<code>
        """
        if not re.match(r"^[A-Za-z0-9]+|[A-Za-z0-9]+$", type):
            raise ValueError("type must be in the format <system>|<code>")

        return type

    @validator("nhs_number")
    @classmethod
    def validate_nhs_number(cls, nhs_number: str) -> str:
        """
        Validate the NHS number of the DocumentPointer
        The NHS number should be a valid NHS number
        """
        if not is_valid_nhs_number(nhs_number):  # type: ignore
            raise ValueError(f"Not a valid NHS number: {nhs_number}")

        return nhs_number

    @validator("source")
    @classmethod
    def validate_source(cls, source: str) -> str:
        """
        Validate the source of the DocumentPointer
        Should be one of ["NRLF", "NRL"]
        """
        if source not in VALID_SOURCES:
            raise ValueError(f"Not a source: {source}. Expected one of {VALID_SOURCES}")

        return source

    @validator("created_on")
    @classmethod
    def validate_created_on(cls, created_on: str) -> str:
        """
        Validate the created_on of the DocumentPointer
        The created_on should be a valid date
        """
        _date = created_on[:-1] if created_on.endswith("Z") else created_on
        try:
            datetime.fromisoformat(_date)

        except ValueError:
            raise ValueError(f"Not a valid ISO date: {created_on}") from None

        return created_on

    @validator("updated_on")
    @classmethod
    def validate_updated_on(cls, updated_on: Optional[str]) -> Optional[str]:
        """
        Validate the updated_on of the DocumentPointer
        The updated_on should be a valid date
        """
        if updated_on is None:
            return updated_on

        _date = updated_on[:-1] if updated_on.endswith("Z") else updated_on
        try:
            datetime.fromisoformat(_date)

        except ValueError:
            raise ValueError(f"Not a valid ISO date: {updated_on}") from None

        return updated_on

    @property
    def pk(self) -> str:
        """
        Returns the pk (partition key) for the DocumentPointer
        Uses the custodian, custodian suffix (if applicable) and document_id to create the pk

        Examples:
        - D#<custodian>#<custodian_suffix>#<document_id>
        - D#<custodian>#<document_id>
        """
        if self.custodian_suffix:
            return "#".join(
                [
                    DBPrefix.DocumentPointer.value,
                    self.custodian,
                    self.custodian_suffix,
                    self.document_id,
                ]
            )

        return "#".join(
            [DBPrefix.DocumentPointer.value, self.custodian, self.document_id]
        )

    @property
    def sk(self) -> str:
        """
        Returns the sk (sort key) for the DocumentPointer
        Identical to the primary key for DocumentPointer
        """
        return self.pk

    @property
    def pk_1(self) -> str:
        """
        Returns the pk_1 value used for the partition key in the idx_gsi_1 index

        Example: P#<nhs_number>
        """
        return f"{DBPrefix.Patient.value}#{self.nhs_number}"

    @property
    def sk_1(self) -> str:
        """
        Returns the sk_1 value used for the sort key in the idx_gsi_1 index

        Example:
        - CO#<created_on>#<custodian>#<custodian_suffix>#<document_id>
        - CO#<created_on>#<custodian>#<document_id>
        """
        if self.custodian_suffix:
            return "#".join(
                [
                    DBPrefix.CreatedOn.value,
                    self.created_on,
                    self.custodian,
                    self.custodian_suffix,
                    self.document_id,
                ]
            )

        return "#".join(
            [
                DBPrefix.CreatedOn.value,
                self.created_on,
                self.custodian,
                self.document_id,
            ]
        )

    @property
    def pk_2(self) -> str:
        """
        Returns the pk_2 value used for the partition key in the idx_gsi_1 index

        Example:
        - O#<custodian>
        - O#<custodian>#<custodian_suffix>
        """
        if self.custodian_suffix:
            return "#".join(
                [DBPrefix.Organisation.value, self.custodian, self.custodian_suffix]
            )

        return "#".join([DBPrefix.Organisation.value, self.custodian])

    @property
    def sk_2(self) -> str:
        """
        Returns the sk_2 value used for the sort key in the idx_gsi_2 index
        Identical to the sort key for idx_gsi_1
        """
        return self.sk_1

    @classmethod
    def public_alias(cls) -> str:
        return "DocumentReference"
