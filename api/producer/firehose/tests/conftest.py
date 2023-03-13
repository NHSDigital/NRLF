import uuid

import pytest

from api.producer.firehose.tests.e2e_utils import (
    make_good_cloudwatch_data,
    submit_cloudwatch_data_to_firehose,
)
from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json


@pytest.fixture(scope="session")
def global_event_handler():
    return {}


@pytest.fixture(scope="session")
def session():
    return new_aws_session()


@pytest.fixture(scope="session")
def stream_arn():
    firehose_metadata = get_terraform_json()["firehose"]["value"]["producer"][
        "delivery_stream"
    ]
    return firehose_metadata["arn"]


@pytest.fixture(scope="session")
def bucket_name():
    firehose_metadata = get_terraform_json()["firehose"]["value"]["producer"][
        "delivery_stream"
    ]
    return firehose_metadata["s3"]["arn"].replace("arn:aws:s3:::", "")


@pytest.fixture(scope="session")
def prefix_template():
    firehose_metadata = get_terraform_json()["firehose"]["value"]["producer"][
        "delivery_stream"
    ]
    return firehose_metadata["s3"]["prefix"]


@pytest.fixture(scope="session")
def error_prefix_template():
    firehose_metadata = get_terraform_json()["firehose"]["value"]["producer"][
        "delivery_stream"
    ]
    return firehose_metadata["s3"]["error_prefix"].replace(
        "!{firehose:error-output-type}", "processing-failed"
    )


@pytest.fixture
def _submit_good_cloudwatch_data(session, stream_arn, global_event_handler):
    transaction_id = f"good_cloudwatch_data-{uuid.uuid4()}"
    cloudwatch_data = make_good_cloudwatch_data(transaction_id=transaction_id, n_logs=3)
    submit_cloudwatch_data_to_firehose(
        session=session,
        stream_arn=stream_arn,
        cloudwatch_data=cloudwatch_data,
    )
    global_event_handler["good_logs"] = cloudwatch_data.log_events


@pytest.fixture
def _submit_bad_cloudwatch_data(session, stream_arn, global_event_handler):
    transaction_id = f"bad_cloudwatch_data-{uuid.uuid4()}"
    cloudwatch_data = make_good_cloudwatch_data(transaction_id=transaction_id, n_logs=3)
    cloudwatch_data.log_events.append({"value": "this is an invalid log event"})
    submit_cloudwatch_data_to_firehose(
        session=session,
        stream_arn=stream_arn,
        cloudwatch_data=cloudwatch_data,
    )
    global_event_handler["bad_logs"] = cloudwatch_data.log_events


@pytest.fixture
def _submit_very_bad_cloudwatch_data(session, stream_arn, global_event_handler):
    transaction_id = f"very_bad_cloudwatch_data-{uuid.uuid4()}"
    cloudwatch_data = make_good_cloudwatch_data(transaction_id=transaction_id, n_logs=3)
    cloudwatch_data.log_events.append("this is a very bad log event")
    submit_cloudwatch_data_to_firehose(
        session=session,
        stream_arn=stream_arn,
        cloudwatch_data=cloudwatch_data,
    )
    global_event_handler["very_bad_logs"] = cloudwatch_data.log_events
