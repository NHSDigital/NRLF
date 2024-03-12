import json
from io import StringIO
from unittest.mock import Mock

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws
from pytest_mock import MockerFixture

from api.consumer.authoriser.index import get_pointer_types, handler

TEST_EVENT = {
    "type": "REQUEST",
    "methodArn": "arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request",
    "resource": "/request",
    "path": "/request",
    "httpMethod": "GET",
    "headers": {},
    "queryStringParameters": {},
    "pathParameters": {},
    "stageVariables": {"StageVar1": "stageValue1"},
    "requestContext": {
        "path": "/request",
        "accountId": "123456789012",
        "resourceId": "05c7jb",
        "stage": "test",
        "requestId": "...",
        "identity": {},
        "resourcePath": "/request",
        "httpMethod": "GET",
        "apiId": "test-api-id",
    },
}

MOCK_CONTEXT = Mock()


def test_authoriser_happy_path():
    event = TEST_EVENT.copy()
    event["headers"] = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": ["pointer_type"],
                "nrl.ods-code": "X26",
                "nrl.ods-code-extension": "001",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.enable-authorization-lookup": False,
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    result = handler(event, MOCK_CONTEXT)  # type: ignore

    assert result == {
        "context": {"pointer_types": '["pointer_type"]'},
        "principalId": "",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": [
                        "arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request"
                    ],
                }
            ],
        },
    }


def test_authoriser_no_pointer_types():
    event = TEST_EVENT.copy()
    event["headers"] = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": [],
                "nrl.ods-code": "X26",
                "nrl.ods-code-extension": "001",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.enable-authorization-lookup": False,
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    result = handler(event, MOCK_CONTEXT)  # type: ignore

    assert result == {
        "context": {"error": "No pointer types found"},
        "principalId": "",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": [
                        "arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request"
                    ],
                }
            ],
        },
    }


def test_authoriser_no_metadata():
    event = TEST_EVENT.copy()
    event["headers"] = {}

    result = handler(event, MOCK_CONTEXT)  # type: ignore

    assert result == {
        "context": {"error": "No pointer types found"},
        "principalId": "",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": [
                        "arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request"
                    ],
                }
            ],
        },
    }


@mock_aws
def test_authoriser_lookup_from_s3():
    s3 = boto3.client("s3")

    s3.create_bucket(
        Bucket="auth-store",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    s3.put_object(
        Bucket="auth-store", Key="12345/X26.001.json", Body=json.dumps(["pointer_type"])
    )

    event = TEST_EVENT.copy()
    event["headers"] = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": [],
                "nrl.ods-code": "X26",
                "nrl.ods-code-extension": "001",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.enable-authorization-lookup": True,
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    result = handler(event, MOCK_CONTEXT)  # type: ignore

    assert result == {
        "context": {"pointer_types": '["pointer_type"]'},
        "principalId": "",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": [
                        "arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request"
                    ],
                }
            ],
        },
    }


@mock_aws
def test_authoriser_no_s3_key():
    s3 = boto3.client("s3")

    s3.create_bucket(
        Bucket="auth-store",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )

    event = TEST_EVENT.copy()
    event["headers"] = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": [],
                "nrl.ods-code": "X26",
                "nrl.ods-code-extension": "001",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.enable-authorization-lookup": True,
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    result = handler(event, MOCK_CONTEXT)  # type: ignore

    assert result == {
        "context": {"error": "No pointer types found"},
        "principalId": "",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": [
                        "arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request"
                    ],
                }
            ],
        },
    }


def test_get_pointer_types_disabled_authorization_lookup(mocker: MockerFixture):
    s3_mock = Mock()
    boto3_mock = mocker.patch(
        "api.consumer.authoriser.index.boto3.client", return_value=s3_mock
    )

    headers = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": ["test-type"],
                "nrl.ods-code": "X26",
                "nrl.ods-code-extension": "001",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.enable-authorization-lookup": False,
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    pointer_types = get_pointer_types(headers)

    assert pointer_types == ["test-type"]
    assert boto3_mock.called is False


def test_get_pointer_types_enabled_authorization_lookup(mocker: MockerFixture):
    s3_mock = Mock(get_object=Mock(return_value={"Body": StringIO('["s3_pointers"]')}))
    boto3_mock = mocker.patch(
        "api.consumer.authoriser.index.boto3.client", return_value=s3_mock
    )

    headers = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": ["test-type"],
                "nrl.ods-code": "X26",
                "nrl.ods-code-extension": "001",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.enable-authorization-lookup": True,
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    pointer_types = get_pointer_types(headers)

    assert pointer_types == ["s3_pointers"]
    assert boto3_mock.called is True

    s3_mock.get_object.assert_called_once_with(
        Bucket="auth-store", Key="12345/X26.001.json"
    )


def test_get_pointer_types_no_such_key_exception(mocker: MockerFixture):
    s3_mock = Mock(
        get_object=Mock(
            side_effect=ClientError({"Error": {"Code": "NoSuchKey"}}, "get_object")
        )
    )
    boto3_mock = mocker.patch(
        "api.consumer.authoriser.index.boto3.client", return_value=s3_mock
    )

    headers = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": ["test-type"],
                "nrl.ods-code": "X26",
                "nrl.ods-code-extension": "001",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.enable-authorization-lookup": True,
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    pointer_types = get_pointer_types(headers)

    assert pointer_types == []
    assert boto3_mock.called is True

    s3_mock.get_object.assert_called_once_with(
        Bucket="auth-store", Key="12345/X26.001.json"
    )


def test_get_pointer_types_client_error(mocker: MockerFixture):
    s3_mock = Mock(
        get_object=Mock(
            side_effect=ClientError({"Error": {"Code": "SomeError"}}, "get_object")
        )
    )
    boto3_mock = mocker.patch(
        "api.consumer.authoriser.index.boto3.client", return_value=s3_mock
    )

    headers = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": ["test-type"],
                "nrl.ods-code": "X26",
                "nrl.ods-code-extension": "001",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.enable-authorization-lookup": True,
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    with pytest.raises(ClientError) as error:
        get_pointer_types(headers)

    expected_message = (
        "An error occurred (SomeError) when calling the get_object operation: Unknown"
    )
    assert str(error.value) == expected_message

    assert boto3_mock.called is True


def test_get_pointer_types_generic_error(mocker: MockerFixture):
    s3_mock = Mock(get_object=Mock(side_effect=Exception("SomeError")))
    boto3_mock = mocker.patch(
        "api.consumer.authoriser.index.boto3.client", return_value=s3_mock
    )

    headers = {
        "nhsd-connection-metadata": json.dumps(
            {
                "nrl.pointer-types": ["test-type"],
                "nrl.ods-code": "X26",
                "nrl.ods-code-extension": "001",
                "nrl.permissions": ["permission1", "permission2"],
                "nrl.enable-authorization-lookup": True,
            }
        ),
        "nhsd-client-rp-details": json.dumps(
            {
                "developer.app.name": "TestApp",
                "developer.app.id": "12345",
            }
        ),
    }

    with pytest.raises(Exception) as error:
        get_pointer_types(headers)

    expected_message = "SomeError"
    assert str(error.value) == expected_message

    assert boto3_mock.called is True
