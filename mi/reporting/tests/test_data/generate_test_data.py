import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from random import choice, randint
from string import ascii_letters, digits
from typing import Type

import fire

PATH_TO_TEST_DATA = Path(__file__).parent / "test_data.json"
UPPERCASE_SEARCH = re.compile("[A-Z][^A-Z]*")
ASCII = ascii_letters + digits


def generate_random_string(length=10):
    return "".join(choice(ASCII) for _ in range(length))


def camel_to_snake(camel: str):
    return "_".join(UPPERCASE_SEARCH.findall(camel)).lower()


class Dimension:
    @classmethod
    def name(cls) -> str:
        return f"dimension.{camel_to_snake(cls.__name__)}"


@dataclass
class Measure:
    provider_id: str
    patient_id: str
    document_type_id: str
    day: int
    month: int
    year: int
    day_of_week: int
    count_created: int
    count_deleted: int

    @classmethod
    def name(cls):
        return f"fact.{camel_to_snake(cls.__name__)}"


@dataclass
class Provider(Dimension):
    provider_id: str
    provider_suffix: str = field(default_factory=generate_random_string)
    provider_name: str = field(default_factory=generate_random_string)


@dataclass
class Patient(Dimension):
    patient_id: str
    patient_hash: str = field(default_factory=generate_random_string)


@dataclass
class DocumentType(Dimension):
    document_type_id: str
    document_type_code: str = field(default_factory=generate_random_string)
    document_type_system: str = field(default_factory=generate_random_string)


FOREIGN_KEYS: dict[str, Type[Dimension]] = {
    "provider_id": Provider,
    "patient_id": Patient,
    "document_type_id": DocumentType,
}


def _generate_measures(n: int) -> list[dict]:
    measures = []
    while len(measures) < n:
        measure = Measure(
            provider_id=randint(0, 5),
            patient_id=randint(0, 5),
            document_type_id=randint(0, 2),
            day=randint(1, 31),
            month=randint(1, 12),
            year=randint(2021, 2028),
            day_of_week=randint(0, 6),
            count_created=randint(1, 30),
            count_deleted=randint(1, 30),
        )
        measures.append(asdict(measure))
    return measures


def _generate_required_foreign_keys(measures: list[dict]) -> list[dict[str, Dimension]]:
    foreign_keys = defaultdict(list)
    _foreign_keys: dict[str, dict[str, object]] = defaultdict(dict)
    for measure in measures:
        for field_name, model in FOREIGN_KEYS.items():
            key = measure[field_name]
            if key in _foreign_keys[field_name]:
                continue
            fk = model(**{field_name: key})
            _foreign_keys[field_name][key] = fk
            foreign_keys[model.name()].append(asdict(fk))
    return foreign_keys


def generate_test_data(n: int = 100):
    measures = _generate_measures(n=n)
    foreign_keys = _generate_required_foreign_keys(measures=measures)
    data = {Measure.name(): measures, **foreign_keys}
    with open(PATH_TO_TEST_DATA, "w") as f:
        json.dump(obj=data, fp=f)


if __name__ == "__main__":
    fire.Fire(generate_test_data)
