from csv import QUOTE_NONNUMERIC, DictReader

import pytest

from helpers.aws_session import new_session_from_env
from helpers.terraform import get_terraform_json
from mi.reporting.report import make_report
from mi.reporting.resources import get_credentials, get_endpoint, get_lambda_name
from mi.sql_query.model import Response, Sql, SqlQueryEvent, Status


def get_seed_sql_statement(data: list[dict]) -> Sql:
    field_names = list(data[0].keys())
    id_field = "id"

    _parametrised_values = []
    params = {}
    for i, row in enumerate(data):
        param_names = []
        for field_name in field_names:
            _param_name = f"{field_name}_{i}"
            params[_param_name] = row[field_name]
            param_names.append(_param_name)
        _parametrised_values.append(
            "(" + ", ".join(f"%({_name})s" for _name in param_names) + ")"
        )

    identifiers = {f"field_{i}": name for i, name in enumerate(field_names)}
    _parametrised_field_names = ", ".join(f"{{{field_i}}}" for field_i in identifiers)
    _update_fields = ", ".join(
        f"{field_i} = EXCLUDED.{field_i}"
        for field_i in field_names
        if field_i != id_field
    )
    _parametrised_values = "\n\t".join(_parametrised_values)
    statement = f"""INSERT INTO my_table ({_parametrised_field_names})
                    VALUES {_parametrised_values}
                    ON CONFLICT ({id_field})
                    DO UPDATE SET {_update_fields};"""
    return Sql(statement=statement, identifiers=identifiers, params=params)


def seed_database(data: list[dict], workspace: str, environment: str):
    session = new_session_from_env(env=environment)
    credentials = get_credentials(
        session=session, workspace=workspace, operation="write"
    )
    endpoint = get_endpoint(session=session, env=environment, operation="write")
    sql = get_seed_sql_statement(data=data)
    event = SqlQueryEvent(
        sql=sql,
        endpoint=endpoint,
        **credentials,
    )

    function_name = get_lambda_name(workspace=workspace)
    client = session.client("lambda")
    raw_response = client.invoke(FunctionName=function_name, Payload=event.json())
    response = Response.parse_raw(raw_response["Payload"].read())
    assert response.status == Status.OK, response.outcome


@pytest.mark.integration
def test_make_report():
    tf_json = get_terraform_json()
    environment = tf_json["account_name"]["value"]
    workspace = tf_json["workspace"]["value"]

    input_data = [{"id": 12345, "num": 34567, "data": "foo"}]
    report_aliases = {"id": "Identifier", "data": "Data"}

    seed_database(data=input_data, workspace=workspace, environment=environment)
    out_path = make_report(env=environment, workspace=workspace)
    with open(out_path) as f:
        out_data = list(DictReader(f=f, quoting=QUOTE_NONNUMERIC))

    for row in input_data:
        for original, alias in report_aliases.items():
            row[alias] = row.pop(original)
        assert row in out_data, f"Could not find {row} in output data ({out_path})"
