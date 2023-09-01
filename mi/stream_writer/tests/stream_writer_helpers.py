import json

from mi.stream_writer.tests.paths import PATH_TO_TEST_DATA


def dynamodb_stream_event(
    unique_id: str, created_on: str, image_type: str, event_name: str
) -> dict:
    event_path = PATH_TO_TEST_DATA / "dynamodb_stream_event.json"
    with open(event_path) as file:
        event_str = file.read()
    event_str = event_str.replace("<<UNIQUE_ID>>", unique_id)
    event_str = event_str.replace("<<CREATED_ON>>", created_on)
    event_str = event_str.replace("<<EVENT_NAME>>", event_name)
    event_str = event_str.replace("<<IMAGE_TYPE>>", image_type)
    return json.loads(event_str)  # noqa
