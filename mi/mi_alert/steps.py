import requests

DUMMY_URL = "http://example.com"


def parse_event(event: dict) -> tuple[str, str]:
    (record,) = event["Records"]
    bucket_name = record["s3"]["bucket"]["name"]
    file_key = record["s3"]["object"]["key"]
    return bucket_name, file_key


def read_body(s3_client: str, bucket_name: str, file_key: str) -> bytes:
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    return response["Body"].read()


def send_notification(slack_webhook_url, **data):
    try:
        (slack_webhook_url,) = slack_webhook_url
    except ValueError:
        slack_webhook_url = DUMMY_URL

    response = requests.post(url=slack_webhook_url, json=data)
    return response.text
