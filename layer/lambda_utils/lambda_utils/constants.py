from logging import ERROR, INFO


class LoggingOutcomes:
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ERROR = "ERROR"


class LoggingConstants:
    TO_MILLISECONDS = 1000
    JSON_INDENT = 2
    RESERVED_FIELDS = ["self", "logger", "context", "dependencies", "event"]
    REDACTED = "REDACTED"


class LogLevel:
    INFO = INFO
    ERROR = ERROR
