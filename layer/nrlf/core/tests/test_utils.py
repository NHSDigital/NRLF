from datetime import datetime, timezone
from re import match

from freezegun import freeze_time

from layer.nrlf.core.utils import create_fhir_instant

# FHIR INSTANT refex taken from the spec: https://www.hl7.org/fhir/datatypes.html#instant
SPEC_REGEX = r"([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]{1,9})?(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))"


@freeze_time("2021-01-01")
def test_create_fhir_instant_with_time():
    time = datetime(2022, 1, 1, 12, 0, 0, 0, timezone.utc)

    result = create_fhir_instant(time)

    assert result == "2022-01-01T12:00:00.000000Z"
    assert match(SPEC_REGEX, result) != None


@freeze_time("2021-01-01")
def test_create_fhir_instant_no_time():
    result = create_fhir_instant()

    assert result == "2021-01-01T00:00:00.000000Z"
    assert match(SPEC_REGEX, result) != None
