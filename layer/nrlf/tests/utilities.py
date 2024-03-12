import json
import pathlib
from typing import Any

DATA_DIR = pathlib.Path(__file__).parent / "data"


def load_data_file(file_name: str) -> str:
    """
    Load a resource from a file
    """
    file_path = DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} not found")

    if not file_path.is_file():
        raise ValueError(f"{file_path} is not a file")

    return file_path.read_text(encoding="utf-8")


def load_json_file(file_name: str) -> Any:
    """
    Load a JSON resource from a file
    """
    return json.loads(load_data_file(file_name))
