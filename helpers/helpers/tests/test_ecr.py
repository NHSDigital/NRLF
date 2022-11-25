import base64
from unittest import mock

import pytest

from helpers.ecr import get_ecr_password


@pytest.fixture
def authorization_data():
    return {
        "authorizationData": [
            {
                "authorizationToken": base64.b64encode(b"foo:bar"),
                "expiresAt": "2022-05-17T06:56:13.652000+00:00",
                "proxyEndpoint": "https://012345678910.dkr.ecr.us-east-1.amazonaws.com",
            }
        ]
    }


@mock.patch("helpers.ecr.new_aws_session")
def test_get_ecr_password(mocked_new_aws_session, authorization_data):
    mocked_new_aws_session().client().get_authorization_token.return_value = (
        authorization_data
    )
    assert get_ecr_password() == "bar"
