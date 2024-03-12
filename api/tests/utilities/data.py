import pathlib
from typing import Type

from nrlf.core.types import DocumentReference
from nrlf.producer.fhir.r4 import model as producer_model

DATA_DIR = pathlib.Path(__file__).parent / "../data"


def load_document_reference_data(file_name: str) -> str:
    file_path = DATA_DIR / "DocumentReference" / f"{file_name}.json"

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return file_path.read_text()


def load_document_reference(
    file_name: str, model: Type[DocumentReference] = producer_model.DocumentReference
):
    contents = load_document_reference_data(file_name)
    return model.parse_raw(contents)
