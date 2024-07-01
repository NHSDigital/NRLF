#!/usr/bin/env python
import json
from os import path
from pathlib import Path

import boto3
import fire

AWS_ACCOUNT_FOR_ENV = {
    "dev": "dev",
    "qa": "test",
    "ref": "test",
    "int": "test",
    "prod": "prod",
}

POINTER_TYPES = [
    "http://snomed.info/sct|736253002",
    "http://snomed.info/sct|1363501000000100",
    "http://snomed.info/sct|1382601000000107",
    "http://snomed.info/sct|325691000000100",
    "http://snomed.info/sct|736373009",
    "http://snomed.info/sct|861421000000109",
    "http://snomed.info/sct|887701000000100",
]


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


def add_test_files(folder, file_name, local_path):
    print("Adding test files to temporary directory...")
    folder_path = Path.joinpath(local_path, folder)
    # Create all folders in the path
    folder_path.mkdir(parents=True, exist_ok=True)
    file_path = Path.joinpath(folder_path, file_name)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(POINTER_TYPES, f)


def add_test_files1(application_id, ods_code, permissions_file):
    print("Adding test files to temporary directory...")
    with open(permissions_file, "a") as f:
        print(
            f"This is what we will save: \n[{application_id}]\n{ods_code} = {POINTER_TYPES}"
        )
        f.write(f"\n[{application_id}]\n")
        f.write(f"{ods_code} = {POINTER_TYPES}")


def download_files(s3_client, bucket_name, local_path, file_names, folders):
    print(f"Downloading {len(file_names)} S3 files to temporary directory...")
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

    add_test_files("K6PerformanceTest", "Y05868.json", local_path)


def main(env: str, path_to_store: str):
    bucket = f"nhsd-nrlf--{env}--authorization-store"
    account_id = get_account_id(env)

    boto_session = get_boto_session_for_account(account_id)

    permissions_path = Path(
        path.abspath(path.join(path_to_store + "/nrlf_permissions"))
    )
    permissions_path.mkdir(parents=True, exist_ok=True)
    permissions_file_path = permissions_path.joinpath("permissions.toml")

    s3 = boto_session.client("s3")
    s3.download_file(bucket, permissions_file_path.name, str(permissions_file_path))
    add_test_files1("K6PerformanceTest", "Y05868", str(permissions_file_path))
    # files, folders = get_file_folders(s3, bucket)

    # download_files(
    #     s3,
    #     bucket,
    #     path.abspath(path.join(path_to_store + "/nrlf_permissions")),
    #     files,
    #     folders,
    # )
    print("Downloaded S3 permissions...")


if __name__ == "__main__":
    fire.Fire(main)
