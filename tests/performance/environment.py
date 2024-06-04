# flake8: noqa
import json
import pathlib
from uuid import uuid4

import boto3
import fire
from nhs_number import generate

from nrlf.core.constants import POINTER_TYPES
from nrlf.core.dynamodb.repository import DocumentPointer
from nrlf.core.logger import logger
from nrlf.tests.data import load_document_reference

logger.setLevel("ERROR")

DYNAMODB = boto3.resource("dynamodb", region_name="eu-west-2")


class LogReference:
    pass


def _generate_record(nhs_number: str, pointer_type: str, ods_code: str):
    doc_ref = load_document_reference("Y05868-736253002-Valid")

    pointer_type_description = POINTER_TYPES[pointer_type]

    doc_ref.id = f"{ods_code}-{uuid4()}"
    doc_ref.subject.identifier.value = nhs_number  # type: ignore
    doc_ref.type.coding[0].code = pointer_type  # type: ignore
    doc_ref.type.coding[0].display = pointer_type_description  # type: ignore

    return doc_ref


def _generate_records(patient_count: int, documents_per_type: int, ods_code: str):
    for _ in range(patient_count):
        (nhs_number,) = generate()
        for pointer_type in POINTER_TYPES.keys():
            for _ in range(documents_per_type):
                yield _generate_record(nhs_number, pointer_type, ods_code)


def setup(
    env: str,
    patient_count: int = 100,
    documents_per_type: int = 10,
    ods_code: str = "Y05868",
    out: str = "tests/performance/reference-data.json",
    output_full_pointers: bool = False,
):
    print(f"Creating Test Data in environment '{env}'")

    print(f"Patient Count: {patient_count}")
    print(f"Documents Per Type: {documents_per_type}")

    table = DYNAMODB.Table(f"nhsd-nrlf--{env}--document-pointer")
    documents = {}
    nhs_numbers = set()

    with table.batch_writer() as batch:
        for record in _generate_records(patient_count, documents_per_type, ods_code):
            pointer = DocumentPointer.from_document_reference(record)
            batch.put_item(Item=pointer.dict())

            documents[pointer.id] = record.dict(exclude_none=True)
            nhs_numbers.add(pointer.nhs_number)

    print(f"Created {len(documents)} documents for {len(nhs_numbers)} patients")

    if output_full_pointers:
        output = json.dumps({"documents": documents, "nhs_numbers": list(nhs_numbers)})
    else:
        output = json.dumps(
            {"pointer_ids": list(documents.keys()), "nhs_numbers": list(nhs_numbers)}
        )

    output_path = pathlib.Path(out)
    output_path.write_text(output)
    print(f"Output written to {output_path}")


def cleanup(env: str, input: str = "tests/performance/reference-data.json"):
    input_path = pathlib.Path(input)
    data = json.loads(input_path.read_text())

    if "documents" in data:
        pointer_ids = data["documents"].keys()
    else:
        pointer_ids = data["pointer_ids"]

    print(f"Cleaning up {len(pointer_ids)} document pointers in environment '{env}'")
    table = DYNAMODB.Table(f"nhsd-nrlf--{env}--document-pointer")
    with table.batch_writer() as batch:
        for id in pointer_ids:
            ods_code, document_id = id.split("-", maxsplit=1)
            pk = f"D#{ods_code}#{document_id}"
            batch.delete_item(Key={"pk": pk, "sk": pk})

    print("Cleanup complete")


if __name__ == "__main__":
    fire.Fire()
