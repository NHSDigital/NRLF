from enum import Enum


class LogReference(Enum):
    PARSE_EVENT = "Parsing S3 bucket and key from event"
    READ_BODY = "Reading event body from S3 bucket and key"
    PARSE_BODY = "Parsing event body as JSON"
    IS_ERROR_EVENT = "Checking whether this is a true error event"
    SEND_NOTIFICATION = "Sending notification"


# These can be found here: https://docs.aws.amazon.com/firehose/latest/dev/monitoring-with-cloudwatch-logs.html
SPLUNK_CONNECTION_CLOSED = "Splunk.ConnectionClosed"
SPLUNK_BAD_PROXY = "Splunk.ProxyWithoutStickySessions"
SPLUNK_SERVER_ERROR = "Splunk.ServerError"
SPLUNK_ACK_TIMEOUT = "Splunk.AckTimeout"
SPLUNK_CONNECTION_TIMEOUT = "Splunk.ConnectionTimeout"
SPLUNK_INDEXER_BUSY = "Splunk.IndexerBusy"  # this one is completely undocumented

FLAKY_SPLUNK_ERROR_CODES = (
    SPLUNK_CONNECTION_CLOSED,
    SPLUNK_BAD_PROXY,
    SPLUNK_INDEXER_BUSY,
    SPLUNK_SERVER_ERROR,
    SPLUNK_ACK_TIMEOUT,
    SPLUNK_CONNECTION_TIMEOUT,
)

DUMMY_URL = "http://example.com"
