import json
import uuid

import pytest

from firehose.processor.tests.e2e_utils import make_good_cloudwatch_data
from helpers.aws_session import new_aws_session
from helpers.firehose import submit_cloudwatch_data_to_firehose
from helpers.terraform import get_terraform_json
from nrlf.core.validators import json_loads


@pytest.fixture(scope="session")
def global_event_handler():
    return {}


@pytest.fixture
def s3_client():
    session = new_aws_session()
    return session.client("s3")


@pytest.fixture
def firehose_client():
    session = new_aws_session()
    return session.client("firehose")


@pytest.fixture
def firehose_metadata():
    return get_terraform_json()["firehose"]["value"]["processor"]["delivery_stream"]


@pytest.fixture
def stream_arn(firehose_metadata):
    return firehose_metadata["arn"]


@pytest.fixture
def bucket_name(firehose_metadata):
    return firehose_metadata["s3"]["arn"].replace("arn:aws:s3:::", "")


@pytest.fixture
def prefix_template(firehose_metadata):
    return firehose_metadata["s3"]["prefix"]


@pytest.fixture
def error_prefix_template(firehose_metadata):
    return firehose_metadata["s3"]["error_prefix"].replace(
        "!{firehose:error-output-type}", "processing-failed"
    )


@pytest.fixture
def _submit_good_cloudwatch_data(firehose_client, stream_arn, global_event_handler):
    transaction_id = f"good_cloudwatch_data-{uuid.uuid4()}"
    cloudwatch_data = make_good_cloudwatch_data(transaction_id=transaction_id, n_logs=3)
    submit_cloudwatch_data_to_firehose(
        firehose_client=firehose_client,
        stream_arn=stream_arn,
        cloudwatch_data=cloudwatch_data,
    )
    global_event_handler["good_logs"] = [
        json_loads(log_event["message"])
        for log_event in cloudwatch_data.dict()["log_events"]
    ]


@pytest.fixture
def _submit_bad_cloudwatch_data(firehose_client, stream_arn, global_event_handler):
    transaction_id = f"bad_cloudwatch_data-{uuid.uuid4()}"
    cloudwatch_data = make_good_cloudwatch_data(transaction_id=transaction_id, n_logs=3)
    new_log_event = cloudwatch_data.log_events[0].copy(
        update={"message": json.dumps({"value": "this is an invalid log event"})}
    )
    cloudwatch_data.log_events.append(new_log_event)
    submit_cloudwatch_data_to_firehose(
        firehose_client=firehose_client,
        stream_arn=stream_arn,
        cloudwatch_data=cloudwatch_data,
    )
    global_event_handler["bad_logs"] = [
        json_loads(log_event["message"])
        for log_event in cloudwatch_data.dict()["log_events"]
    ]


@pytest.fixture
def _submit_very_bad_cloudwatch_data(firehose_client, stream_arn, global_event_handler):
    transaction_id = f"very_bad_cloudwatch_data-{uuid.uuid4()}"
    cloudwatch_data = make_good_cloudwatch_data(transaction_id=transaction_id, n_logs=3)
    very_bad_logs = [
        json_loads(log_event["message"])
        for log_event in cloudwatch_data.dict()["log_events"]
    ]

    very_bad_message = "this is a very bad log event"
    new_log_event = cloudwatch_data.log_events[0].copy(
        update={"message": very_bad_message}
    )
    cloudwatch_data.log_events.append(new_log_event)
    very_bad_logs.append(very_bad_message)

    submit_cloudwatch_data_to_firehose(
        firehose_client=firehose_client,
        stream_arn=stream_arn,
        cloudwatch_data=cloudwatch_data,
    )
    global_event_handler["very_bad_logs"] = very_bad_logs
