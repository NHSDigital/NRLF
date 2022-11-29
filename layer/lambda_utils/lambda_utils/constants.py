import os
from logging import ERROR, INFO


class HttpStatusCodes:
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500


class LoggingOutcomes:
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ERROR = "ERROR"


class LoggingConstants:
    TO_MILLISECONDS = 1000
    JSON_INDENT = 2
    RESERVED_FIELDS = ["self", "logger", "context", "dependencies", "event"]


class LogLevel:
    INFO = INFO
    ERROR = ERROR


class ApiRequestLevel:
    USER_RESTRICTED = "user_restricted"
    APP_RESTRICTED = "app_restricted"


class AUTHORISER_CONTEXT_FIELDS:
    X_CORRELATION_ID = "x-correlation-id"
    NHSD_CORRELATION_ID = "nhsd-correlation-id"
    REQUEST_TYPE = "request-type"
    CLIENT_APP_NAME = "developer.app.name"
    CLIENT_APP_ID = "developer.app.id"
    SHARING_CODE = "nhsd-remote-sharing-code"
    AUTHORISED_TARGETS = "authorised-targets"
    ACCEPT_HEADER = "accept"


RUNNING_IN_LOCALSTACK = "LOCALSTACK_HOSTNAME" in os.environ
