import math
import re
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Union

from .header_config import AcceptHeader

VERSION_RE = re.compile(r"v(\d+)")
API_ROOT_DIRNAME = "api"
VERSIONED_HANDLER_GLOB = "src/v*/handler.py"


class VersionException(Exception):
    pass


def get_version_from_header(event) -> str:
    accept_header = AcceptHeader(event)
    return accept_header.version


def get_largest_possible_version(
    requested_version: str, possible_versions: list[str]
) -> str:
    integer_versions = map(int, possible_versions)
    possible_versions = [
        version
        for version in integer_versions
        if int(float(requested_version)) >= version
    ]
    largest_possible_version = max(possible_versions, default=math.inf)
    if not math.isfinite(largest_possible_version):
        raise VersionException("Version not supported")
    return str(largest_possible_version)


def _module_path_from_file_path(file_path: Path):
    path = str(file_path.parent / file_path.stem)
    path_relative_to_api_root = Path(path[path.find(API_ROOT_DIRNAME) :])
    return ".".join(path_relative_to_api_root.parts)


def get_versioned_steps(file_path: Union[Path, str]) -> dict[str:ModuleType]:
    versions_paths = Path(file_path).parent.glob(VERSIONED_HANDLER_GLOB)
    versioned_steps = {}
    for file_path in versions_paths:
        (version_number,) = VERSION_RE.match(file_path.parent.name).groups()
        module_path = _module_path_from_file_path(file_path)
        versioned_handler = import_module(module_path)
        versioned_steps[version_number] = versioned_handler.steps
    return versioned_steps
