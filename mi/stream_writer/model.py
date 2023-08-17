import os
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime as dt
from enum import Enum
from typing import Optional, TypeVar

from pydantic import BaseModel

from mi.stream_writer.constants import PATH_TO_QUERIES, TYPE_SEPARATOR, DateTimeFormats
from mi.stream_writer.utils import hash_nhs_number, to_snake_case


class Environment(BaseModel):
    POSTGRES_DATABASE_NAME: str
    RDS_CLUSTER_HOST: str
    RDS_CLUSTER_PORT: int
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str

    @classmethod
    def construct(cls) -> "Environment":
        return cls(**os.environ)


class SecretsManagerCache:
    def __init__(self, client):
        self.client = client
        self.secret = None

    def get_secret(self, secret_id):
        if self.secret is None:
            raw_secret = self.client.get_secret_value(SecretId=secret_id)
            self.secret = AwsSecret(**raw_secret).SecretString
        return self.secret


@dataclass
class AwsSecret:
    ARN: str
    Name: str
    VersionId: str
    SecretString: str
    SecretBinary: Optional[bytes] = None
    VersionStages: Optional[list[str]] = None
    CreatedDate: Optional[dt] = None
    ResponseMetadata: Optional[dict] = None


class DynamodbEventImageType(str, Enum):
    OLD_IMAGE = "OldImage"
    NEW_IMAGE = "NewImage"


class Action(str, Enum):
    CREATED = "created"
    DELETED = "deleted"


class DynamoDBEventConfig(BaseModel):
    """Model to map a DynamoDb Stream Image Type on to a query file"""

    image_type: DynamodbEventImageType
    action: Action

    @property
    def sql(self):
        with open(f"{PATH_TO_QUERIES}/{self.action}.sql") as f:
            return f.read()


class Dimension:
    def __init__(self, **kwargs):
        """init that sets dataclass properties and ignores extra kwargs"""
        named_fields = set(f.name for f in fields(self))
        for field_name, value in kwargs.items():
            if field_name in named_fields:
                setattr(self, field_name, value)

    @property
    def sql(self):
        file_name = to_snake_case(camel_case=self.__class__.__name__)
        with open(f"{PATH_TO_QUERIES}/dimensions/{file_name}.sql") as f:
            return f.read()


@dataclass(init=False)
class DocumentType(Dimension):
    document_type_system: str
    document_type_code: str


@dataclass(init=False)
class Patient(Dimension):
    patient_hash: str


@dataclass(init=False)
class Provider(Dimension):
    provider_name: str


DimensionType = TypeVar("DimensionType", bound=Dimension)


@dataclass
class RecordParams:
    """
    Model which maps on to the INSERT fields in
    mi/stream_writer/queries/{action}.sql

    Note that these fields correspond to the volatile
    Fact and Dimension data, as found in
    mi/schema/schema.sql
    """

    provider_name: str
    patient_hash: str
    document_type_system: str
    document_type_code: str
    created_date: str
    created_date_weekday: str

    @classmethod
    def from_document_pointer(
        cls,
        type: str,
        custodian: str,
        custodian_suffix: str,
        nhs_number: str,
        created_on: str,
        **_,  # <-- this will ignore all other DocumentPointer fields
    ):
        """Constructor for RecordParams directly from DocumentPointer fields"""
        system, value = type.split(TYPE_SEPARATOR)
        date_time = dt.strptime(created_on, DateTimeFormats.DOCUMENT_POINTER_FORMAT)
        created_date = date_time.strftime(DateTimeFormats.FACT_FORMAT)
        created_date_weekday = date_time.weekday()
        patient_hash = hash_nhs_number(nhs_number=nhs_number)
        provider_name = custodian
        if custodian_suffix:
            provider_name += f"-{custodian_suffix}"
        return cls(
            provider_name=provider_name,
            patient_hash=patient_hash,
            document_type_system=system,
            document_type_code=value,
            created_date=created_date,
            created_date_weekday=created_date_weekday,
        )

    def to_dimension(self, dimension_type: type[DimensionType]) -> DimensionType:
        # The Dimension base constructor will ignore excess kwargs, so the following
        # will pull any required fields from RecordParams into the provided DimensionType
        return dimension_type(**asdict(self))


class Status(str, Enum):
    OK = "OK"
    ERROR = "ERROR"


@dataclass
class ErrorResponse:
    error: str
    error_type: str
    function: str
    trace: str
    status: Status = Status.ERROR
    metadata: dict = field(default_factory=dict)


@dataclass
class GoodResponse:
    status: Status = Status.OK
    records_processed: dict[str, int] = None


DIMENSION_TYPES = (DocumentType, Patient, Provider)
