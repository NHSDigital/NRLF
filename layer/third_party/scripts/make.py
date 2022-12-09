import re
from pathlib import Path

import sh
from build_scripts.layer_build import build_third_party

path_to_zip = Path(__file__).parent.parent / "dist" / "third_party.zip"


def escape_ansi(line):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


def change_detected(file: str):
    result = sh.git("diff", "--quiet", "main", "--", file, _ok_code=[0, 1, 128])
    return result.exit_code == 1


if __name__ == "__main__":
    if change_detected("pyproject.toml") or not path_to_zip.exists():
        build_third_party(__file__)
    else:
        print(
            f"Skipping rebuild of {path_to_zip} since no changes detected from 'main'"
        )
