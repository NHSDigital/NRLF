import pytest
from nrlf.core.authoriser_response import authorisation_denied, authorisation_ok


@pytest.mark.parametrize(
    ["principal_id", "resource", "context"],
    (
        ["principal", "read_lambda", {"headers1": "header:1"}],
        ["principal", "read_lambda", {"headers1": "header1", "headers2": "header2"}],
    ),
)
def test_authorised_ok(principal_id, resource, context):
    result = authorisation_ok(principal_id, resource, context)
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
    result = authorisation_denied(principal_id, resource, context)
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
