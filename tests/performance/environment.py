# flake8: noqa
import json
import pathlib
from uuid import uuid4

import boto3
import fire
from nhs_number import generate

from nrlf.core.dynamodb.repository import DocumentPointer
from nrlf.core.logger import logger
from nrlf.tests.data import load_document_reference

logger.setLevel("ERROR")

DYNAMODB = boto3.resource("dynamodb", region_name="eu-west-2")


class LogReference:
    pass


POINTER_TYPES = {
    "736253002": "Mental Health Crisis Plan",
    "1363501000000100": "Royal College of Physicians NEWS2 (National Early Warning Score 2) chart",
    "1382601000000107": "ReSPECT (Recommended Summary Plan for Emergency Care and Treatment) form",
    "325691000000100": "Contingency plan",
    "736373009": "End of life care plan",
    "861421000000109": "End of Life Care Coordination Summary",
    "887701000000100": "Emergency Health Care Plans",
}


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
    output = json.dumps({"documents": documents, "nhs_numbers": list(nhs_numbers)})

    output_path = pathlib.Path(out)
    output_path.write_text(output)
    print(f"Output written to {output_path}")


def cleanup(env: str, input: str = "tests/performance/reference-data.json"):
    input_path = pathlib.Path(input)
    data = json.loads(input_path.read_text())

    documents = data["documents"]

    print(f"Cleaning up {len(documents)} document pointers in environment '{env}'")
    table = DYNAMODB.Table(f"nhsd-nrlf--{env}--document-pointer")
    with table.batch_writer() as batch:
        for id in documents.keys():
            ods_code, document_id = id.split("-", maxsplit=1)
            pk = f"D#{ods_code}#{document_id}"
            batch.delete_item(Key={"pk": pk, "sk": pk})

    print("Cleanup complete")


if __name__ == "__main__":
    fire.Fire()
