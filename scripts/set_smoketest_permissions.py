#!/usr/bin/env python
import json
from os import path
from pathlib import Path

import fire
from aws_session_assume import get_boto_session


def main(env: str = "dev", stack_name: str = "dev"):
    boto_session = get_boto_session(env)

    print("Getting smoke test parameters from AWS....")  # noqa
    smoke_test_params_name = f"nhsd-nrlf--{env}--smoke-test-parameters"
    secretsmanager = boto_session.client("secretsmanager", region_name="eu-west-2")
    smoke_test_params_value = secretsmanager.get_secret_value(
        SecretId=smoke_test_params_name
    )

    print("Parsing parameters....")  # noqa
    smoke_test_params = json.loads(smoke_test_params_value["SecretString"])
    nrlf_app_id = smoke_test_params["nrlf_app_id"]
    ods_code = smoke_test_params["ods_code"]

    print(f"Adding {ods_code} permissions to {nrlf_app_id} app in S3....")  # noqa
    bucket = f"nhsd-nrlf--{stack_name}-authorization-store"
    s3 = boto_session.client("s3")
    s3.put_object(
        Bucket=bucket,
        Key=f"{nrlf_app_id}/{ods_code}.json",
        Body=open(f"./tests/smoke/permissions/{ods_code}.json", "rb"),
    )


if __name__ == "__main__":
    fire.Fire(main)
