from datetime import datetime, timezone


# TODO-NOW - Add unit test for create_fhir_instant
def create_fhir_instant(time: datetime = datetime.now(tz=timezone.utc)) -> str:
    """
    Creates a timestamp string to represent the current time in the
    <instant> format defined by the FHIR spec:
    https://www.hl7.org/fhir/datatypes.html#instant
    """
    return time.isoformat(timespec="milliseconds") + "Z"
