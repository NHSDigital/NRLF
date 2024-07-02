#!/usr/bin/env python
import json
from os import path
from pathlib import Path

import fire
from aws_session_assume import get_boto_session

POINTER_TYPES = [
    "http://snomed.info/sct|736253002",
    "http://snomed.info/sct|1363501000000100",
    "http://snomed.info/sct|1382601000000107",
    "http://snomed.info/sct|325691000000100",
    "http://snomed.info/sct|736373009",
    "http://snomed.info/sct|861421000000109",
    "http://snomed.info/sct|887701000000100",
]


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
    bucket = f"nhsd-nrlf--{env}-authorization-store"
    boto_session = get_boto_session(env)

    s3 = boto_session.client("s3")
    files, folders = get_file_folders(s3, bucket)

    download_files(
        s3,
        bucket,
        path.abspath(path.join(path_to_store + "/nrlf_permissions")),
        files,
        folders,
    )
    print("Downloaded S3 permissions...")


if __name__ == "__main__":
    fire.Fire(main)
