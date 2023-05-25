from enum import Enum


class LogReference(Enum):
    PARSE_EVENT = "Parsing S3 bucket and key from event"
    READ_BODY = "Reading event body from S3 bucket and key"
    PARSE_BODY = "Parsing event body as JSON"
    IS_ERROR_EVENT = "Checking whether this is a true error event"
    SEND_NOTIFICATION = "Sending notification"


SPLUNK_CONNECTION_CLOSED = "Splunk.ConnectionClosed"
SPLUNK_BAD_PROXY = "Splunk.ProxyWithoutStickySessions"
SPLUNK_INDEXER_BUSY = "Splunk.IndexerBusy"
FLAKY_SPLUNK_ERROR_CODES = (
    SPLUNK_CONNECTION_CLOSED,
    SPLUNK_BAD_PROXY,
    SPLUNK_INDEXER_BUSY,
)

DUMMY_URL = "http://example.com"
