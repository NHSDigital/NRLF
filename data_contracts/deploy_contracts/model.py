import re
from dataclasses import asdict, dataclass
from pathlib import Path

from nrlf.core.constants import DbPrefix
from nrlf.core.json_schema import DEFAULT_SYSTEM_VALUE
from nrlf.core.model import Contract, key

from .constants import GLOBAL, HTTP_SUBS, PATH_PATTERNS
from .errors import BadContractGroup, BadContractPath


def _substitute_http_from_system(system: str):
    for path_system, url_system in HTTP_SUBS.items():
        if path_system in system:
            return system.replace(path_system, url_system)
    return system


def _strip_http_from_system(system: str):
    for path_system, url_system in HTTP_SUBS.items():
        if url_system in system:
            return system.replace(url_system, path_system)
    return system


@dataclass
class ContractGroup:
    name: str
    system: str = DEFAULT_SYSTEM_VALUE
    value: str = DEFAULT_SYSTEM_VALUE

    def __post_init__(self):
        if (
            self.system == DEFAULT_SYSTEM_VALUE or self.value == DEFAULT_SYSTEM_VALUE
        ) and (self.system != self.value):
            raise BadContractGroup(
                f"system and value must both be equal to either be '{DEFAULT_SYSTEM_VALUE}' or "
                f"otherwise neither must be equal to '{DEFAULT_SYSTEM_VALUE}'"
            )

    @property
    def pk(self):
        return key(DbPrefix.Contract, self.system, self.value)

    @property
    def active_sk(self):
        return key(DbPrefix.Version, 0, self.name)

    def __hash__(self):
        return (self.system, self.value, self.name).__hash__()

    def dict(self):
        return asdict(self)

    @classmethod
    def from_contract(cls, contract: Contract) -> "ContractGroup":
        return cls(
            system=contract.system.__root__,
            value=contract.value.__root__,
            name=contract.name.__root__,
        )

    def to_active_contract(self, version: str, json_schema: dict) -> Contract:
        return Contract(
            pk=self.pk,
            sk=self.active_sk,
            version=version,
            json_schema=json_schema,
            **self.dict(),
        )

    @classmethod
    def from_path(cls, path: str) -> "ContractGroup":
        for regex in PATH_PATTERNS:
            match: re.Match = regex.match(str(path))
            if match:
                kwargs = match.groupdict()
                system = kwargs.get("system")
                if system:
                    kwargs["system"] = _substitute_http_from_system(system=system)
                return ContractGroup(**kwargs)

        raise BadContractPath(
            f"File path '{path}' not one of the expected formats: "
            + " or ".join(regex.pattern for regex in PATH_PATTERNS)
        )

    def to_path(self, base_dir: str) -> Path:
        if self.system == DEFAULT_SYSTEM_VALUE and self.value == DEFAULT_SYSTEM_VALUE:
            base_path = (GLOBAL,)
        else:
            system = _strip_http_from_system(self.system)
            base_path = (system, self.value)
        return Path(base_dir).joinpath(*base_path, f"{self.name}.json")
