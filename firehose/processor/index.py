import os
from pathlib import Path

import boto3
from aws_lambda_powertools.utilities.parser.models.kinesis_firehose import (
    KinesisFirehoseModel,
)
from lambda_utils.logging import Logger, prepare_default_event_for_logging
from nrlf.core.firehose.handler import firehose_handler
from pydantic import BaseModel


class Config(BaseModel):
    """
    Defines all the Environment Variables that are needed for
    the business logic to execute successfully.
    """

    AWS_REGION: str
    PREFIX: str
    ENVIRONMENT: str
    SPLUNK_INDEX: str
    SOURCE: str


CONFIG = Config(
    **{env_var: os.environ.get(env_var) for env_var in Config.__fields__.keys()}
)
BOTO3_FIREHOSE_CLIENT = boto3.client("firehose")


def handler(event, context):
    logger = Logger(
        logger_name=Path(__file__).stem,
        aws_lambda_event=prepare_default_event_for_logging(),
        aws_environment=CONFIG.ENVIRONMENT,
        splunk_index=CONFIG.SPLUNK_INDEX,
        source=CONFIG.SOURCE,
    )
    firehose_event = KinesisFirehoseModel(**event)
    lambda_result = firehose_handler(
        event=firehose_event,
        boto3_firehose_client=BOTO3_FIREHOSE_CLIENT,
        logger=logger,
    )
    return lambda_result.dict()
