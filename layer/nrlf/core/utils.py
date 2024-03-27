from datetime import datetime, timezone


def create_fhir_instant(time: datetime = None) -> str:
    """
    Creates a timestamp string to represent the current time in the
    <instant> format defined by the FHIR spec:
    https://www.hl7.org/fhir/datatypes.html#instant
    """

    if time is None:
        time = datetime.now(timezone.utc)

    return time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
