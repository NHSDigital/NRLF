import json
import pathlib
from typing import Type

from nrlf.core.types import DocumentReference
from nrlf.producer.fhir.r4 import model as producer_model

DATA_DIR = pathlib.Path(__file__).parent / "../../../tests/data/"
FILE_CACHE = {}


def load_document_reference_data(file_name: str) -> str:
    file_path = DATA_DIR / "DocumentReference" / f"{file_name}.json"

    if file_path in FILE_CACHE:
        return FILE_CACHE[file_path]

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    FILE_CACHE[file_path] = file_path.read_text()
    return FILE_CACHE[file_path]


def load_document_reference_json(file_name: str) -> dict:
    contents = load_document_reference_data(file_name)
    return json.loads(contents)


def load_document_reference(
    file_name: str, model: Type[DocumentReference] = producer_model.DocumentReference
):
    contents = load_document_reference_data(file_name)
    return model.model_validate_json(contents)
