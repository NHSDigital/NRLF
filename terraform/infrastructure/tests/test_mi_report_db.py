import json

import pytest

from helpers.aws_session import new_aws_session
from helpers.terraform import get_terraform_json
from mi.sql_query.model import Response, Sql, SqlQueryEvent, Status
from nrlf.core.validators import json_loads

SELECT_SQL = Sql(statement="SELECT * FROM my_table;")
INSERT_SQL = Sql(
    statement="INSERT INTO my_table (id, num, data) VALUES (1, 2.3, 'a') ON CONFLICT (id) DO NOTHING;"
)
DELETE_SQL = Sql(statement="DELETE FROM my_table WHERE id=1;")


@pytest.fixture(scope="session")
def assume_account_id():
    tf_json = get_terraform_json()
    return tf_json["assume_account_id"]["value"]


@pytest.fixture(scope="session")
def session(assume_account_id):
    return new_aws_session(account_id=assume_account_id)


@pytest.fixture(scope="session")
def prefix():
    tf_json = get_terraform_json()
    return tf_json["prefix"]["value"]


@pytest.fixture(scope="session")
def environment():
    tf_json = get_terraform_json()
    return tf_json["workspace"]["value"]


@pytest.fixture(scope="session")
def read_secret_name(prefix: str, environment: str):
    return f"{prefix}--{environment}--read_password"


@pytest.fixture(scope="session")
def write_secret_name(prefix: str, environment: str):
    return f"{prefix}--{environment}--write_password"


@pytest.fixture(scope="session")
def function_name(prefix):
    return f"{prefix}--mi--sql_query"


@pytest.fixture(scope="session")
def secrets_client(session):
    return session.client("secretsmanager")


@pytest.fixture(scope="session")
def lambda_client(session):
    return session.client("lambda")


@pytest.fixture(scope="session")
def read_password(secrets_client, read_secret_name):
    return secrets_client.get_secret_value(SecretId=read_secret_name)["SecretString"]


@pytest.fixture(scope="session")
def read_user(environment):
    return f"{environment}-read"


@pytest.fixture(scope="session")
def write_password(secrets_client, write_secret_name):
    return secrets_client.get_secret_value(SecretId=write_secret_name)["SecretString"]


@pytest.fixture(scope="session")
def write_user(environment):
    return f"{environment}-write"


@pytest.fixture(scope="session")
def endpoint():
    tf_json = get_terraform_json()
    return tf_json["mi"]["value"]["endpoint"]


def invoke_lambda(
    client, function_name: str, user: str, password: str, endpoint: str, sql: Sql
) -> Response:
    event = SqlQueryEvent(user=user, password=password, endpoint=endpoint, sql=sql)
    _event = event.dict()
    _response = client.invoke(FunctionName=function_name, Payload=json.dumps(_event))
    _response_body = json_loads(_response["Payload"].read())
    return Response(**_response_body)


@pytest.mark.integration
@pytest.mark.parametrize(
    ("sql", "expected_response"),
    (
        [SELECT_SQL, Status.OK],
        [INSERT_SQL, Status.ERROR],
        [DELETE_SQL, Status.ERROR],
    ),
)
def test_read_user_permissions(
    sql,
    expected_response,
    lambda_client,
    function_name,
    read_user,
    read_password,
    endpoint,
):
    response = invoke_lambda(
        client=lambda_client,
        function_name=function_name,
        user=read_user,
        password=read_password,
        endpoint=endpoint,
        sql=sql,
    )
    assert response.status is expected_response


@pytest.mark.integration
@pytest.mark.parametrize(
    ("sql", "expected_response"),
    (
        [SELECT_SQL, Status.OK],
        [INSERT_SQL, Status.OK],
        [DELETE_SQL, Status.ERROR],
    ),
)
def test_write_user_permissions(
    sql,
    expected_response,
    lambda_client,
    function_name,
    write_user,
    write_password,
    endpoint,
):
    response = invoke_lambda(
        client=lambda_client,
        function_name=function_name,
        user=write_user,
        password=write_password,
        endpoint=endpoint,
        sql=sql,
    )
    assert response.status is expected_response, response.outcome
