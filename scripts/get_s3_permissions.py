#!/usr/bin/env python
import json
from os import path
from pathlib import Path

import boto3
import fire

from nrlf.core.constants import PERMISSIONS_FILENAME, PointerTypes

AWS_ACCOUNT_FOR_ENV = {
    "dev": "dev",
    "qa": "test",
    "ref": "test",
    "int": "test",
    "prod": "prod",
}


def get_account_id(env: str):
    if env not in AWS_ACCOUNT_FOR_ENV:
        raise ValueError(f"Invalid environment: {env}")

    account_name = AWS_ACCOUNT_FOR_ENV[env]
    secretsmanager = boto3.client("secretsmanager", region_name="eu-west-2")
    secret_id = f"nhsd-nrlf--mgmt--{account_name}-account-id"
    result = secretsmanager.get_secret_value(SecretId=secret_id)
    account_id = result["SecretString"]

    return account_id


def get_boto_session_for_account(account_id: str):
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


def main(env: str, path_to_store: str):
    bucket = f"nhsd-nrlf--{env}--authorization-store"
    account_id = get_account_id(env)

    boto_session = get_boto_session_for_account(account_id)

    permissions_path = Path(
        path.abspath(path.join(path_to_store + "/nrlf_permissions"))
    )
    permissions_path.mkdir(parents=True, exist_ok=True)
    permissions_file_path = permissions_path.joinpath(PERMISSIONS_FILENAME)

    s3 = boto_session.client("s3")
    s3.download_file(bucket, permissions_file_path.name, str(permissions_file_path))
    print("Downloaded S3 permissions...")


if __name__ == "__main__":
    fire.Fire(main)
