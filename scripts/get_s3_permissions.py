#!/usr/bin/env python
from os import path
from pathlib import Path

import boto3
import fire

_DEFAULT_APP_DEV = "4e41d2d9-3ef6-48dc-8406-5faba77ffd83"
_DEFAULT_APP_PROD = "7a4ad8c7-3927-4259-af7b-ac9d305a86ad"
_DEFAULT_APP_FOR_APIGEE_ENV = {
    "internal-dev": _DEFAULT_APP_DEV,
    "internal-dev-sandbox": _DEFAULT_APP_DEV,
    "internal-qa": _DEFAULT_APP_DEV,
    "internal-qa-sandbox": _DEFAULT_APP_DEV,
    "ref": _DEFAULT_APP_DEV,
    "int": _DEFAULT_APP_PROD,
    "int-sandbox": _DEFAULT_APP_PROD,
    "prod": _DEFAULT_APP_PROD,
}

_NRL_SYNC_APP_DEV = "94492ef7-40a5-47bb-a18b-b9023bd4ec9a"
_NRL_SYNC_APP_PROD = "f9822096-11ec-479f-8d95-fcc8dd22048d"
_NRL_SYNC_APP_FOR_APIGEE_ENV = {
    "internal-dev": _NRL_SYNC_APP_DEV,
    "internal-qa": _NRL_SYNC_APP_DEV,
    "ref": _NRL_SYNC_APP_DEV,
    "int": _NRL_SYNC_APP_PROD,
    "prod": _NRL_SYNC_APP_PROD,
}

AWS_ACCOUNT_FOR_ENV = {
    "dev": "dev",
    "qa": "test",
    "ref": "test",
    "int": "test",
    "prod": "prod",
}
APIGEE_ENV_FOR_ENV = {
    "dev": "internal-dev",
    "dev-sandbox": "internal-dev-sandbox",
    "qa": "internal-qa",
    "qa-sandbox": "internal-qa-sandbox",
    "ref": "ref",
    "int": "int",
    "int-sandbox": "sandbox",
    "prod": "prod",
}
APP_FOR_ALIAS = {
    "default": _DEFAULT_APP_FOR_APIGEE_ENV,
    "nrl_sync": _NRL_SYNC_APP_FOR_APIGEE_ENV,
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


def get_file_folders(s3_client, bucket_name, prefix=""):

    print("Getting file folders to download...")
    file_names = []
    folders = []

    default_kwargs = {"Bucket": bucket_name, "Prefix": prefix}
    next_token = ""

    while next_token is not None:
        updated_kwargs = default_kwargs.copy()
        if next_token != "":
            updated_kwargs["ContinuationToken"] = next_token

        response = s3_client.list_objects_v2(**updated_kwargs)
        contents = response.get("Contents")

        for result in contents:
            key = result.get("Key")
            if key[-1] == "/":
                folders.append(key)
            else:
                file_names.append(key)

        next_token = response.get("NextContinuationToken")

    return file_names, folders


def download_files(s3_client, bucket_name, local_path, file_names, folders):
    print(f"Downloading {len(file_names)} S3 files to temporary direrectory...")
    local_path = Path(local_path)

    for folder in folders:
        folder_path = Path.joinpath(local_path, folder)
        # Create all folders in the path
        folder_path.mkdir(parents=True, exist_ok=True)

    for file_name in file_names:
        file_path = Path.joinpath(local_path, file_name)
        # Create folder for parent directory
        file_path.parent.mkdir(parents=True, exist_ok=True)
        s3_client.download_file(bucket_name, file_name, str(file_path))


def main(env: str):
    bucket = f"nhsd-nrlf--{env}--authorization-store"
    account_id = get_account_id(env)

    boto_session = get_boto_session_for_account(account_id)

    s3 = boto_session.client("s3")
    files, folders = get_file_folders(s3, bucket)

    download_files(s3, bucket, path.abspath(path.join("/tmp/s3")), files, folders)
    print(f"Downloaded S3 permissions...")


if __name__ == "__main__":
    fire.Fire(main)
