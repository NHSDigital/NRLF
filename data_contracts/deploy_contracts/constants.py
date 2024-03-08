import re
from pathlib import Path
from types import MappingProxyType

from nrlf.core_pipeline.constants import DbPrefix

EMPTY_SCHEMA = MappingProxyType({})

GLOBAL = "global"

_PATH_TO_CONTRACTS_ROOT = Path(__file__).parent.parent
PATHS_TO_CONTRACTS = list(_PATH_TO_CONTRACTS_ROOT.glob("**/*json"))
PATH_PATTERNS = (
    re.compile(
        rf"(?:[a-zA-Z0-9_\-\/]*?){_PATH_TO_CONTRACTS_ROOT}\/{GLOBAL}\/(?P<name>[a-zA-Z0-9_\-]+)\.json$"
    ),
    re.compile(
        rf"(?:[a-zA-Z0-9_\-\/]*?){_PATH_TO_CONTRACTS_ROOT}\/(?P<system>[a-zA-Z0-9_\-\/\.]+?)\/(?P<value>[a-zA-Z0-9_\-]+)\/(?P<name>[a-zA-Z0-9_\-]+)\.json$"
    ),
)
CONTRACT_PK_WILDCARD = DbPrefix.Contract.value
VERSION_SEPARATOR = "."

HTTP_SUBS = {
    "http/": "http://",
    "https/": "https://",
}
