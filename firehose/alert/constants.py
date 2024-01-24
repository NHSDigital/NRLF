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
