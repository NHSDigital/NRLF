from functools import cache
from pathlib import Path

from nrlf.core.validators import json_loads

terraform_output_json_path = str(
    Path(__file__).parent.parent.parent / "terraform" / "infrastructure" / "output.json"
)


@cache
def get_terraform_json() -> dict:
    with open(terraform_output_json_path, "r") as f:
        return json_loads(f.read())
