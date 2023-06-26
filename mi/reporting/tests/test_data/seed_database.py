import json
from pathlib import Path
from typing import Generator, Type, Union

import fire

from helpers.aws_session import new_aws_session
from helpers.log import log
from helpers.terraform import get_terraform_json
from mi.reporting.resources import get_credentials, get_endpoint, get_lambda_name
from mi.reporting.tests.test_data.generate_test_data import (
    FOREIGN_KEYS,
    Dimension,
    Measure,
)
from mi.sql_query.model import Response, Sql, SqlQueryEvent, Status

PATH_TO_HERE = Path(__file__).parent


def _get_test_data(test_id: str) -> dict:
    with open(PATH_TO_HERE / "test_data.json") as f:
        data = json.load(f)
    for item in data[Measure.name()]:
        item["partition_key"] = test_id
        for fk in FOREIGN_KEYS.keys():
            item[fk] += "-" + test_id
    for fk, model in FOREIGN_KEYS.items():
        for item in data[model.name()]:
            item[fk] += "-" + test_id
    return data


def _item_to_sql(item: dict, model: Type[Union[Dimension, Measure]]):
    identifiers, params = {}, {}
    for i, (field_name, field_value) in enumerate(item.items()):
        alias = f"field_{i}"
        identifiers[alias] = field_name
        params[alias] = field_value
    field_alias_str = ", ".join(f"{{{alias}}}" for alias in identifiers)
    value_alias_str = ", ".join(f"%({alias})s" for alias in identifiers)
    schema_name, table_name = model.name().split(".")
    return Sql(
        statement=f"INSERT INTO {{schema_name}}.{{table_name}} ({field_alias_str}) VALUES ({value_alias_str})",
        identifiers={
            **identifiers,
            "schema_name": schema_name,
            "table_name": table_name,
        },
        params=params,
    )


def _convert_data_to_sql_insert(data: dict) -> Generator[Sql, None, None]:
    for model in FOREIGN_KEYS.values():
        for item in data[model.name()]:
            yield _item_to_sql(item=item, model=model)
    for item in data[Measure.name()]:
        yield _item_to_sql(item=item, model=Measure)


def _seed_database(data: dict, workspace: str, environment: str, account_id: str):
    session = new_aws_session(account_id=account_id)
    credentials = get_credentials(
        session=session, workspace=workspace, operation="write"
    )
    function_name = get_lambda_name(workspace=workspace)
    client = session.client("lambda")

    endpoint = get_endpoint(session=session, env=environment, operation="write")
    for sql in _convert_data_to_sql_insert(data):
        event = SqlQueryEvent(
            sql=sql,
            endpoint=endpoint,
            **credentials,
        )
        raw_response = client.invoke(FunctionName=function_name, Payload=event.json())
        response = Response.parse_raw(raw_response["Payload"].read())
        assert response.status == Status.OK, response.outcome


@log("Created seed data for {test_id}")
def run_seed_database(test_id: str):
    tf_json = get_terraform_json()
    environment = tf_json["account_name"]["value"]
    workspace = tf_json["workspace"]["value"]
    account_id = tf_json["assume_account_id"]["value"]

    data = _get_test_data(test_id=test_id)
    _seed_database(
        data=data,
        environment=environment,
        workspace=workspace,
        account_id=account_id,
    )


def seed_database(test_id: str):
    run_seed_database(test_id=test_id)


if __name__ == "__main__":
    fire.Fire(seed_database)
