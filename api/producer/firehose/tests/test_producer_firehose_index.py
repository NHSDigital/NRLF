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

import base64
import gzip
import json
from datetime import datetime, timedelta

import pytest

from api.producer.firehose.tests.e2e_utils import (
    MAX_RUNTIME,
    parse_prefix,
    retrieve_firehose_output,
)


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.firehose
def test_firehose_output(
    session,
    bucket_name,
    prefix_template,
    error_prefix_template,
    global_event_handler,
    _submit_good_cloudwatch_data,
    _submit_bad_cloudwatch_data,
    _submit_very_bad_cloudwatch_data,
):
    assert (
        len(global_event_handler) == 3
    )  # Sanity check: cloudwatch events have been submitted

    # Some setup
    start_time = datetime.utcnow()
    possible_prefixes = set(
        parse_prefix(prefix=prefix, time=time)
        for prefix in (prefix_template, error_prefix_template)
        for time in (start_time, start_time + timedelta(seconds=MAX_RUNTIME))
    )

    # Conditions we will test
    verify_good_cloudwatch_data = False
    verify_bad_cloudwatch_data = False
    verify_very_bad_cloudwatch_data = False

    # NB the following loops for 600 secs then fails unless
    # the final break statement is executed
    for prefix, file_data in retrieve_firehose_output(
        s3_client=session.client("s3"),
        bucket_name=bucket_name,
        start_time=start_time,
        possible_prefixes=possible_prefixes,
    ):
        if prefix.startswith("processed"):
            if (not verify_good_cloudwatch_data) and all(
                log_event in file_data
                for log_event in global_event_handler["good_logs"]
            ):
                print("Verified good cloudwatch data")
                verify_good_cloudwatch_data = True
        elif prefix.startswith("error"):
            for error_event in file_data:
                parsed_cloudwatch_data = json.loads(
                    gzip.decompress(base64.b64decode(error_event["rawData"]))
                )
                print("Parsed cloudwatch data", parsed_cloudwatch_data)
                if (not verify_bad_cloudwatch_data) and (
                    parsed_cloudwatch_data["logEvents"]
                    == global_event_handler["bad_logs"]
                ):
                    print("Verified bad cloudwatch data")
                    verify_bad_cloudwatch_data = True
                if (not verify_very_bad_cloudwatch_data) and (
                    parsed_cloudwatch_data["logEvents"]
                    == global_event_handler["very_bad_logs"]
                ):
                    print("Verified very bad cloudwatch data")
                    verify_very_bad_cloudwatch_data = True

        # The test has passed if all conditions have been met
        if all(
            (
                verify_good_cloudwatch_data,
                verify_bad_cloudwatch_data,
                verify_very_bad_cloudwatch_data,
            )
        ):
            break
