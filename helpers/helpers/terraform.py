import json
from pathlib import Path

terraform_output_json_path = str(
    Path(__file__).parent.parent.parent / "terraform" / "infrastructure" / "output.json"
)


def get_terraform_json() -> dict:
    with open(terraform_output_json_path, "r") as f:
        return json.loads(f.read())
