from typing import Dict

from api.consumer.readDocumentReference.src.versioning import AcceptHeader

from .header_config import AcceptHeader

import math


class VersionException(Exception):
    pass


def get_version_from_header(event) -> str:
    accept_header = AcceptHeader(event)
    return accept_header.version


def get_steps(requested_version: str, handler_versions: Dict[str, any]):
    version = get_largest_possible_version(requested_version, handler_versions)
    return handler_versions[version]


def get_largest_possible_version(
    requested_version: str, handler_versions: Dict[str, any]
) -> str:
    all_versions = [int(key) for key in handler_versions]
    possible_versions = [
        version for version in all_versions if int(requested_version) >= version
    ]
    largest_possible_version = max(possible_versions, default=math.inf)
    if not math.isfinite(largest_possible_version):
        raise VersionException("Version not supported")
    return str(largest_possible_version)
