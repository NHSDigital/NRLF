import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from nhs_number import is_valid as is_valid_nhs_number
from pydantic import BaseModel, Field, PrivateAttr, root_validator, validator

from nrlf.core.constants import SYSTEM_SHORT_IDS, VALID_SOURCES
from nrlf.core.logger import LogReference, logger
from nrlf.core.types import DocumentReference
from nrlf.core.utils import create_fhir_instant


class DBPrefix(str, Enum):
    DocumentPointer = "D"
    Patient = "P"
    CreatedOn = "CO"
    Organisation = "O"
    Category = "C"
    Type = "T"
    MasterIdentifier = "MI"


def get_id_for_system(system: str, attr_placement: str) -> str | None:
    """
    Get the id for a given system
    """
    if system not in SYSTEM_SHORT_IDS:
        # TODO-NOW - Log this -logger.log(LogReference.DOCPOINTER006, system=system)
        raise ValueError(f"Unsupported system defined in {attr_placement}")

    return SYSTEM_SHORT_IDS.get(system)


KEBAB_CASE_RE = re.compile(r"(?<!^)(?=[A-Z])")


class DynamoDBModel(BaseModel):
    _from_dynamo: bool = PrivateAttr(default=False)

    def __init__(self, **data):
        super().__init__(**data)
        self._from_dynamo = data.get("_from_dynamo", False)

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
    category_id: str
    category: str
    type_id: str
    type: str
    master_identifier: Optional[str] = None
    author: str
    source: str
    version: int
    document: str
    created_on: str
    updated_on: Optional[str] = None
    document_id: str = Field(exclude=True)
    schemas: list = Field(default_factory=list)

    def dict(self, **kwargs) -> dict:
        """
        Override dict() to include partition and sort keys
        """
        default_dict = super().dict(**kwargs)
        return {
            **default_dict,
            **self.indexes,
        }

    @classmethod
    def from_document_reference(
        cls, resource: DocumentReference, created_on: Optional[str] = None
    ) -> "DocumentPointer":
        resource_id = getattr(resource, "id")

        # Get identifiers
        subject_identifier = getattr(resource.subject, "identifier")
        custodian_identifier = getattr(resource.custodian, "identifier")
        if not resource.author or len(resource.author) != 1:
            raise ValueError("DocumentReference.author must have exactly one item")
        author_identifier = getattr(resource.author[0], "identifier")

        # Get identifier values
        nhs_number = getattr(subject_identifier, "value")
        custodian = getattr(custodian_identifier, "value")
        author = getattr(author_identifier, "value")
        master_identifier = getattr(resource.masterIdentifier, "value", None)

        # Get type fields
        type_coding = getattr(resource.type, "coding")
        if not type_coding or len(type_coding) != 1:
            raise ValueError("DocumentReference.type.coding must have exactly one item")
        pointer_type = f"{type_coding[0].system}|{type_coding[0].code}"
        type_system_id = get_id_for_system(
            type_coding[0].system, "DocumentReference.type.coding[0].system"
        )
        type_id = f"{type_system_id}-{type_coding[0].code}"

        # Get category fields
        if not resource.category or len(resource.category) != 1:
            raise ValueError("DocumentReference.category must have exactly one item")
        category_coding = getattr(resource.category[0], "coding")
        if not category_coding or len(category_coding) != 1:
            raise ValueError(
                "DocumentReference.category.coding must have exactly one item"
            )
        pointer_category = f"{category_coding[0].system}|{category_coding[0].code}"
        category_system_id = get_id_for_system(
            category_coding[0].system, "DocumentReference.category.coding[0].system"
        )
        category_id = f"{category_system_id}-{category_coding[0].code}"

        core_model = cls(
            producer_id=None,  # type: ignore - handled by validators
            document_id=None,  # type: ignore - handled by validators
            id=resource_id,
            nhs_number=nhs_number,
            custodian=custodian,
            author=author,
            master_identifier=master_identifier,
            type=pointer_type,
            type_id=type_id,
            category=pointer_category,
            category_id=category_id,
            source="NRLF",
            version=1,
            document=resource.json(exclude_none=True),
            created_on=created_on or create_fhir_instant(),
        )

        logger.log(
            LogReference.DOCPOINTER005,
            producer_id=core_model.producer_id,
            document_id=core_model.document_id,
            type=pointer_type,
        )
        return core_model

    @root_validator(pre=True)
    @classmethod
    def extract_custodian_suffix(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the custodian suffix if it is not provided and the custodian
        is in the format <custodian>.<custodian_suffix>
        """
        logger.log(LogReference.DOCPOINTER001)

        custodian = values.get("custodian")
        custodian_suffix = values.get("custodian_suffix")

        if custodian and not custodian_suffix:
            split_custodian = custodian.split(".")

            if len(split_custodian) == 2:
                custodian, custodian_suffix = split_custodian
                values["custodian"] = custodian

        if custodian_suffix is not None:
            values["custodian_suffix"] = custodian_suffix

        logger.log(
            LogReference.DOCPOINTER002,
            custodian=values["custodian"],
            custodian_suffix=values.get("custodian_suffix"),
        )

        return values

    @root_validator(pre=True)
    @classmethod
    def inject_producer_id(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject the producer_id into the DocumentPointer if it is not provided
        """
        logger.log(LogReference.DOCPOINTER003)

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

        logger.log(
            LogReference.DOCPOINTER004, producer_id=producer_id, document_id=document_id
        )
        return values

    @validator("id")
    @classmethod
    def validate_id(cls, id_: str) -> str:
        """
        Validate the id of the DocumentPointer
        The id should be in the format <producer_id|producer_suffix>-<document_id>
        """
        if not re.match(
            r"^(?=.{1,64}$)[A-Za-z0-9|\\.]+-[A-Za-z0-9]+[A-Za-z0-9\\_\\-]*$", id_
        ):
            raise ValueError("id must be in the format <producer_id>-<document_id>")

        return id_

    @validator("producer_id")
    @classmethod
    def validate_producer_id(cls, producer_id: str, values: Dict[str, Any]) -> str:
        id_ = values.get("id")
        custodian = values.get("custodian_id")
        custodian_suffix = values.get("custodian_suffix")

        if custodian and custodian_suffix:
            if tuple(producer_id.split(".")) != (custodian, custodian_suffix):
                raise ValueError(
                    f"Producer ID {producer_id} (extracted from '{id_}') is not correctly formed. "
                    "It is expected to be composed in the form '<custodian_id>.<custodian_suffix>'"
                )

        elif custodian and producer_id != custodian:
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
    def indexes(self) -> Dict[str, str]:
        indexes = {
            "pk": self.pk,
            "sk": self.sk,
            "patient_key": self.patient_key,
            "patient_sort": self.patient_sort,
        }

        if self.masterid_key:
            indexes["masterid_key"] = self.masterid_key

        return indexes

    @property
    def pk(self) -> str:
        """
        Returns the pk (partition key) for the DocumentPointer
        """
        return "#".join([DBPrefix.DocumentPointer.value, self.id])

    @property
    def sk(self) -> str:
        """
        Returns the sk (sort key) for the DocumentPointer
        """
        return "#".join([DBPrefix.DocumentPointer.value, self.id])

    @property
    def patient_key(self) -> str:
        """
        Returns the patient gsi pk (partition key) for the DocumentPointer
        TODO-NOW: Add docs
        """
        return "#".join([DBPrefix.Patient.value, self.nhs_number])

    @property
    def patient_sort(self) -> str:
        """
        Returns the patient gsi sk (sort key) for the DocumentPointer
        TODO-NOW: Add docs
        """
        return "#".join(
            [
                DBPrefix.Category.value,
                self.category_id,
                DBPrefix.Type.value,
                self.type_id,
                DBPrefix.CreatedOn.value,
                self.created_on,
                DBPrefix.DocumentPointer.value,
                self.id,
            ]
        )

    @property
    def masterid_key(self) -> str | None:
        """
        Returns the doc_key for the DocumentPointer
        TODO-NOW: Add docs
        """
        if not self.master_identifier:
            return None

        return "#".join(
            [
                DBPrefix.Organisation.value,
                self.custodian,
                DBPrefix.MasterIdentifier.value,
                self.master_identifier,
            ]
        )

    @classmethod
    def public_alias(cls) -> str:
        return "DocumentReference"
