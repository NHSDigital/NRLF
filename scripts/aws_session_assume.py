#!/usr/bin/env python
import boto3

_AWS_ACCOUNT_FOR_ENV = {
    "dev": "dev",
    "qa": "test",
    "ref": "test",
    "int": "test",
    "prod": "prod",
}


def _get_account_id(env: str):
    if env not in _AWS_ACCOUNT_FOR_ENV:
        raise ValueError(f"Invalid environment: {env}")

    account_name = _AWS_ACCOUNT_FOR_ENV[env]
    secretsmanager = boto3.client("secretsmanager", region_name="eu-west-2")
    secret_id = f"nhsd-nrlf--mgmt--{account_name}-account-id"
    result = secretsmanager.get_secret_value(SecretId=secret_id)
    account_id = result["SecretString"]

    return account_id


def get_boto_session(env: str):
    account_id = _get_account_id(env)

    sts = boto3.client("sts", region_name="eu-west-2")
    result = sts.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/terraform",
        RoleSessionName="get-account-id",
        DurationSeconds=900,
    )
    credentials = result["Credentials"]

    return boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )