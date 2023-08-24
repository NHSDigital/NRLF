from datetime import datetime as dt
import random
from typing import Literal
from more_itertools import ichunked

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, Field
from feature_tests.common.repository import FeatureTestRepository
from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json
from nrlf.core.dynamodb_types import convert_value_to_dynamo_format
from nrlf.core.model import DocumentPointer


N_SAMPLES = 100000
CHUNKSIZE = 100
PROPORTION_TO_DELETE = 1 / 4

N_TO_DELETE = int(PROPORTION_TO_DELETE * CHUNKSIZE)

PK = "D#{}"


class DocumentPointerMI(BaseModel):
    pk: str
    sk: str
    type: str = Field(regex=r"^http://snomed\.info/sct\|\d{2}$")
    custodian: str = Field(regex=r"^[A-Z]{1}[0-9]{2}$")
    custodian_suffix: Literal[""]
    nhs_number: str = Field(regex=r"^[0-9]{3}$")
    created_on: int = Field(
        ge=dt(year=2023, month=6, day=1).toordinal(),
        le=dt(year=2023, month=12, day=31).toordinal(),
    )


class Factory(ModelFactory[DocumentPointerMI]):
    __model__ = DocumentPointerMI


def draw_doc_refs(item_number: int) -> tuple[str, dict]:
    pk = PK.format(item_number)
    doc_ref = Factory.build(pk=pk, sk=pk).dict()
    doc_ref["created_on"] = dt.fromordinal(doc_ref["created_on"]).strftime(
        r"%Y-%m-%dT%H:%M:%S.%fZ"
    )
    return doc_ref


def create_many(client, table_name, items):
    transact_items = [
        {
            "Put": {
                "TableName": table_name,
                "Item": {k: convert_value_to_dynamo_format(v) for k, v in item.items()},
                "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
            }
        }
        for item in items
    ]
    return client.transact_write_items(TransactItems=transact_items)


def delete_many(client, table_name, keys):
    transact_items = [
        {
            "Delete": {
                "TableName": table_name,
                "Key": {k: convert_value_to_dynamo_format(v) for k, v in key.items()},
                "ConditionExpression": "attribute_exists(pk) AND attribute_exists(sk)",
            }
        }
        for key in keys
    ]
    return client.transact_write_items(TransactItems=transact_items)


def main():
    session = new_aws_session()
    tf_json = get_terraform_json()

    doc_refs = map(draw_doc_refs, range(N_SAMPLES))
    environment_prefix = f'{tf_json["prefix"]["value"]}--'

    client = session.client("dynamodb")
    table_name = f"{environment_prefix}document-pointer"

    repo = FeatureTestRepository(
        item_type=DocumentPointer, client=client, environment_prefix=environment_prefix
    )
    repo.delete_all()

    for doc_ref_chunk in map(list, ichunked(doc_refs, n=CHUNKSIZE)):
        create_many(items=doc_ref_chunk, client=client, table_name=table_name)

        doc_refs_to_delete = random.sample(population=doc_ref_chunk, k=N_TO_DELETE)
        ids_to_delete = [
            {"pk": doc_ref["pk"], "sk": doc_ref["sk"]} for doc_ref in doc_refs_to_delete
        ]
        delete_many(keys=ids_to_delete, client=client, table_name=table_name)


if __name__ == "__main__":
    main()
