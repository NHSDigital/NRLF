import re
import shutil
from pathlib import Path

from build_scripts.layer_build import build_third_party

path_to_zip = Path(__file__).parent.parent / "dist" / "third_party.zip"
path_to_previous_pyproject_toml = path_to_zip.parent / "pyproject.toml"
path_to_current_pyproject_toml = (
    Path(__file__).parent.parent.parent.parent / "pyproject.toml"
)


def escape_ansi(line):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


def change_detected():
    with open(path_to_previous_pyproject_toml) as f:
        old_pyproject = f.read()
    with open(path_to_current_pyproject_toml) as f:
        new_pyproject = f.read()
    return old_pyproject != new_pyproject


if __name__ == "__main__":
    if (
        not path_to_zip.exists()
        or not path_to_previous_pyproject_toml.exists()
        or change_detected()
    ):
        build_third_party(__file__)
        shutil.copy(
            src=path_to_current_pyproject_toml, dst=path_to_previous_pyproject_toml
        )
    else:
        print(  # noqa: T201
            f"Skipping rebuild of {path_to_zip} since no changes detected in 'pyproject.toml'"
        )
