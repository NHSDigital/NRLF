import json
import re
import sys
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Generator, Union

import boto3
import yaml
from nrlf.core.model import AuthConsumer, AuthProducer
from nrlf.core.repository import Repository

terraform_output_json_path = str(
    Path(__file__).parent.parent / "terraform" / "infrastructure" / "output.json"
)

CHUNK_SIZE = 25
KEBAB_CASE_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _to_kebab_case(name: str) -> str:
    return KEBAB_CASE_RE.sub("-", name).lower()


@cache
def _get_terraform_json() -> dict:
    with open(terraform_output_json_path, "r") as f:
        return json.loads(f.read())


def _get_access_token():
    account_id = _get_terraform_json()["assume_account_id"]["value"]
    sts_client = boto3.client("sts")
    current_time = datetime.utcnow().timestamp()
    response = sts_client.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/terraform",
        RoleSessionName=f"nrlf-feature-test-{current_time}",
    )

    access_key_id = response["Credentials"]["AccessKeyId"]
    secret_access_key = response["Credentials"]["SecretAccessKey"]
    session_token = response["Credentials"]["SessionToken"]
    return access_key_id, secret_access_key, session_token


@cache
def _new_aws_session() -> boto3.Session:
    access_key_id, secret_access_key, session_token = _get_access_token()

    return boto3.Session(
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        aws_session_token=session_token,
    )


def _get_boto3_client(client_name: str):
    session = _new_aws_session()
    return session.client(client_name)


class AuthGenerator:
    def __init__(self, env: str, actor_type: str):
        self.env = env
        self.actor_type = actor_type
        self.client = _get_boto3_client(client_name="dynamodb")
        self.auth_model = self._get_auth_model()
        self.table_name = self._get_table_name()

    def recreate_auths(self):
        self._delete_auths()
        self._create_auths()

    def _delete_auths(self):
        print(f"Deleting existing {self.actor_type}s")
        transact_items = [
            {
                "Delete": {
                    "TableName": self.table_name,
                    "Key": {"id": item["id"]},
                }
            }
            for item in self._scan()
        ]
        for chunk in self._chunk_list(transact_items):
            self.client.transact_write_items(TransactItems=chunk)
        print(f"{self.actor_type}s deleted")

    def _scan(self) -> Generator[dict, None, None]:
        items = []
        start_key_kwargs = {}
        while True:
            response = self.client.scan(
                TableName=self.table_name,
                **start_key_kwargs,
            )
            yield from response["Items"]
            try:
                start_key_kwargs = {"ExclusiveStartKey": response["LastEvaluatedKey"]}
            except KeyError:
                break

        return items

    def _chunk_list(self, list_a, chunk_size=CHUNK_SIZE):
        for i in range(0, len(list_a), chunk_size):
            yield list_a[i : i + chunk_size]

    def _create_auths(self):
        print(f"Creating new {self.actor_type}s")
        environment_prefix = f'{_get_terraform_json()["prefix"]["value"]}--'
        repository = Repository(
            item_type=self.auth_model,
            client=self.client,
            environment_prefix=environment_prefix,
        )

        with open(f"../auths/{self.actor_type}.yml", "r") as strean:
            auths = yaml.safe_load(strean)

            for item in auths:
                auth: Union[AuthProducer, AuthConsumer] = self.auth_model(
                    id=item["organisation_code"],
                    application_id=item["application_id"],
                    pointer_types=[f"{row}" for row in item["document_types"]],
                )
                repository.create(auth)
        print(f"{self.actor_type}s created")

    def _get_auth_model(self):
        auth_model = AuthProducer if self.actor_type == "producer" else AuthConsumer
        return auth_model

    def _get_table_name(self):
        environment_prefix = f'{_get_terraform_json()["prefix"]["value"]}--'
        return f"{environment_prefix}{_to_kebab_case(self.auth_model.__name__)}"


def main(actor_type, env):
    auth_generator = AuthGenerator(actor_type=actor_type, env=env)
    auth_generator.recreate_auths()


if __name__ == "__main__":
    actor_type = ""
    if len(sys.argv) > 1:
        actor_type = sys.argv[1]

    env = ""
    if len(sys.argv) >= 2:
        env = sys.argv[2]

    main(actor_type=actor_type, env=env)
