import re
import sys
from typing import Union

import fire
import yaml
from nrlf.core import model
from nrlf.core.model import AuthConsumer, AuthProducer

from helpers.aws_session import new_aws_session
from helpers.seed_data_repository import SeedDataRepository as BaseRepository
from helpers.terraform import get_terraform_json

CHUNK_SIZE = 25
KEBAB_CASE_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _get_model_name(actor_type: str):
    return f"Auth{actor_type.title()}"


def _get_boto3_client(client_name: str):
    session = new_aws_session()
    return session.client(client_name)


class AuthRepository(BaseRepository):
    def recreate_auths(self, actor_type: str):
        self._delete_auths()
        self._create_auths(actor_type=actor_type)

    def _delete_auths(self):
        print(f"Deleting all auth records")
        self.delete_all()
        print(f"Auth records deleted")

    def _create_auths(self, actor_type: str):
        print("Creating auth records")
        with open(f"{actor_type}.yml", "r") as strean:
            auths = yaml.safe_load(strean)

            for item in auths:
                auth: Union[AuthProducer, AuthConsumer] = self.item_type.parse_obj(item)
                self.create(auth)
        print("Auth records created")


def main(actor_type: str, env: str = ""):
    model_name = _get_model_name(actor_type)
    auth_model = getattr(model, model_name)
    client = _get_boto3_client(client_name="dynamodb")
    environment_prefix = f'{get_terraform_json()["prefix"]["value"]}--'
    auth_generator = AuthRepository(
        item_type=auth_model, client=client, environment_prefix=environment_prefix
    )
    auth_generator.recreate_auths(actor_type=actor_type)


if __name__ == "__main__":
    fire.Fire(main)
