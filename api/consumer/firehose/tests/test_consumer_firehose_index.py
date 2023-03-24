"""
This file contains one function testing three cases in a single pytest.
The reason for this setup is that the Firehose cycle
(event queueing, lambda execution, firehose output) can take 5-7 minutes
and so all test cases are submitted in advance of the test via the fixtures:

    _submit_good_cloudwatch_data,
    _submit_bad_cloudwatch_data,
    _submit_very_bad_cloudwatch_data

The S3 output file prefix and keys can't be known exactly, even at runtime, and
so the relevant parts of S3 must be trawled for output files which appear after a
certain point in time.
"""
import json
from datetime import datetime, timedelta

import pytest

from api.producer.firehose.tests.e2e_utils import (
    MAX_RUNTIME,
    all_logs_are_on_s3,
    parse_prefix,
    retrieve_firehose_output,
)


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.firehose
def test_firehose_output(
    # These are all set in the fixtures in the adjacent conftest.py file
    session,
    bucket_name,
    prefix_template,
    error_prefix_template,
    global_event_handler,
    _submit_good_cloudwatch_data,  # Cloudwatch logs that adhere to the LogTemplate
    _submit_bad_cloudwatch_data,  # Cloudwatch logs that include the wrong template
    _submit_very_bad_cloudwatch_data,  # Cloudwatch logs that include print statements
):
    # Look in the fixtures _submit_[good, bad, very_bad]_cloudwatch_data
    # to see where these are set
    good_logs = global_event_handler["good_logs"]
    bad_logs = global_event_handler["bad_logs"]
    very_bad_logs = global_event_handler["very_bad_logs"]

    # Some setup
    s3_client = session.client("s3")
    start_time = datetime.utcnow()
    possible_s3_key_prefixes = set(
        parse_prefix(prefix=prefix, time=time)
        for prefix in (prefix_template, error_prefix_template)
        for time in (start_time, start_time + timedelta(seconds=MAX_RUNTIME))
    )

    # Conditions we will test
    verify_good_logs = False
    verify_bad_logs = False
    verify_very_bad_logs = False

    # NB the following loops for MAX_RUNTIME secs then fails unless
    # the final break statement is executed
    for prefix, logs_from_s3 in retrieve_firehose_output(
        s3_client=s3_client,
        bucket_name=bucket_name,
        start_time=start_time,
        possible_prefixes=possible_s3_key_prefixes,
    ):
        # Please keep these log lines: these aid debugging for new firehose errors
        print("comparing")  # noqa: T201
        print(json.dumps(good_logs, indent=4))  # noqa: T201
        print("to")  # noqa: T201
        print(json.dumps(logs_from_s3, indent=4))  # noqa: T201
        print()  # noqa: T201
        if prefix.startswith("processed") and all_logs_are_on_s3(
            original_logs=good_logs, logs_from_s3=logs_from_s3
        ):
            verify_good_logs = True
        if prefix.startswith("errors") and all_logs_are_on_s3(
            original_logs=bad_logs, logs_from_s3=logs_from_s3
        ):
            verify_bad_logs = True
        if prefix.startswith("errors") and all_logs_are_on_s3(
            original_logs=very_bad_logs, logs_from_s3=logs_from_s3
        ):
            verify_very_bad_logs = True
        print(verify_good_logs, verify_bad_logs, verify_very_bad_logs)  # noqa: T201
        print("------------------")  # noqa: T201

        # The test has passed if all conditions have been met
        if all((verify_good_logs, verify_bad_logs, verify_very_bad_logs)):
            break
