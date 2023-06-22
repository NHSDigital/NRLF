import json
import os
from unittest import mock

import boto3
import pytest
from lambda_utils.tests.unit.utils import make_aws_event
from moto import mock_s3

from nrlf.core.authoriser import (
    Config,
    _create_policy,
    _parse_list_from_s3,
    _PermissionsLookupError,
    execute_steps,
)

BUCKET = "myBucket"
KEY = "myKey"
PERMISSIONS = ["foo", "bar"]


@pytest.fixture()
def s3_client():
    with mock_s3(), mock.patch.dict(
        os.environ, {"AWS_REGION": "eu-west-2"}, clear=True
    ):
        client = boto3.client("s3", region_name="eu-west-2")
        client.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={
                "LocationConstraint": "eu-west-2",
            },
        )
        yield client


def test__parse_list_from_s3_no_object(s3_client):
    with pytest.raises(_PermissionsLookupError) as exc:
        _parse_list_from_s3(
            s3_client=s3_client,
            bucket=BUCKET,
            key="non-existent-key",
        )
    assert (
        str(exc.value)
        == "No permissions were found for the provided credentials, contact onboarding team."
    )


def test__parse_list_from_s3_bad_json(s3_client):
    s3_client.put_object(Bucket=BUCKET, Key=KEY, Body="not_json".encode())
    with pytest.raises(_PermissionsLookupError) as exc:
        _parse_list_from_s3(
            s3_client=s3_client,
            bucket=BUCKET,
            key=KEY,
        )
    assert str(exc.value) == "Malformed permissions, contact onboarding team."


def test__parse_list_from_s3(s3_client):
    s3_client.put_object(Bucket=BUCKET, Key=KEY, Body=json.dumps(PERMISSIONS).encode())
    permissions = _parse_list_from_s3(
        s3_client=boto3.client("s3"),
        bucket=BUCKET,
        key=KEY,
    )
    assert permissions == PERMISSIONS


@pytest.mark.parametrize(
    ["principal_id", "resource", "context"],
    (
        ["principal", "read_lambda", {"headers1": "header:1"}],
        ["principal", "read_lambda", {"headers1": "header1", "headers2": "header2"}],
    ),
)
def test_authorised_ok(principal_id, resource, context):
    result = _create_policy(
        principal_id=principal_id, resource=resource, context=context, effect="Allow"
    )
    expected = {
        "principalId": principal_id,
        "context": context,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": resource,
                }
            ],
        },
    }

    assert expected == result


@pytest.mark.parametrize(
    ["principal_id", "resource", "context"],
    (
        ["principal", "read_lambda", {"headers1": "header:1"}],
        ["principal", "read_lambda", {"headers1": "header1", "headers2": "header2"}],
    ),
)
def test_authorised_denied(principal_id, resource, context):
    result = _create_policy(
        principal_id=principal_id, resource=resource, context=context, effect="Deny"
    )
    expected = {
        "principalId": principal_id,
        "context": context,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "execute-api:Invoke", "Effect": "Deny", "Resource": resource}
            ],
        },
    }

    assert expected == result


@mock.patch(
    "nrlf.core.authoriser.generate_transaction_id", return_value="a-transaction-id"
)
def test_execute_steps_yields_deny_on_internal_server_error(
    mocked_generate_transaction_id,
):
    event = make_aws_event(methodArn={"methodArn": "an-arn"})
    event["headers"] = None  # This will lead to internal server error

    _, result = execute_steps(
        index_path=__file__,
        event=event,
        context=None,
        config=Config(
            AWS_REGION="a-region",
            PREFIX="a-prefix",
            ENVIRONMENT="an-environment",
            SPLUNK_INDEX="an-index",
            SOURCE="the-lambda-name",
            S3_CLIENT="the-s3-client",
            PERMISSIONS_LOOKUP_BUCKET="a-bucket",
        ),
    )

    assert result == {
        "context": {"error": "Internal Server Error"},
        "policyDocument": {
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": "an-arn",
                }
            ],
            "Version": "2012-10-17",
        },
        "principalId": "a-transaction-id",
    }
