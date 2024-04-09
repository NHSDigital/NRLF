import os
from datetime import datetime

from aws_lambda_powertools import Logger as PowertoolsLogger
from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter
from aws_lambda_powertools.logging.types import LogRecord

from nrlf.core.log_references import LogReference


class SplunkFormatter(LambdaPowertoolsFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.splunk_index = os.getenv("SPLUNK_INDEX", "aws_recordlocator_dev")

    def serialize(self, log: LogRecord) -> str:
        """
        Serialize the log record to JSON to Splunk Event format
        """
        log_time = datetime.fromisoformat(str(log["timestamp"])).timestamp()
        return self.json_serializer(
            {
                "time": log_time,
                "index": self.splunk_index,
                "host": str(log.get("function_name")),
                "source": "lambda",
                "event": log,
            }
        )


class Logger(PowertoolsLogger):
    def log(self, code: LogReference, **kwargs):
        kwargs["log_reference"] = code.name
        match code.value.level:
            case "DEBUG":
                self.debug(code.value.message, stacklevel=3, **kwargs)
            case "INFO":
                self.info(code.value.message, stacklevel=3, **kwargs)
            case "WARN":
                self.warning(code.value.message, stacklevel=3, **kwargs)
            case "ERROR":
                self.error(code.value.message, stacklevel=3, **kwargs)
            case "CRITICAL":
                self.critical(code.value.message, stacklevel=3, **kwargs)
            case "EXCEPTION":
                self.exception(code.value.message, **kwargs)


logger = Logger(logger_formatter=SplunkFormatter())
