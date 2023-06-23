from unittest import mock

import pytest
from lambda_utils.tests.unit.utils import make_aws_event

from nrlf.core.authoriser import Config, _create_policy, execute_steps


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
