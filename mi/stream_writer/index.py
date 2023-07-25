from typing import Union

import boto3

from mi.stream_writer.model import Environment, Outcome, Response, SqlQueryEvent, Status
from mi.stream_writer.psycopg2 import connection, psycopg2
from mi.stream_writer.sql import execute_sql_query


def connect_to_database(**connect_kwargs) -> Union[connection, Response]:
    try:
        conn = psycopg2.connect(**connect_kwargs)
        return conn
    except Exception as err:
        response = Response(
            status=Status.ERROR, outcome=f"{err.__class__.__name__}: {err}"
        )
        return response


def execute_sql(conn: connection, event: SqlQueryEvent):
    cur = conn.cursor()
    try:
        results = execute_sql_query(cursor=cur, sql=event.sql)
    except Exception as err:
        response = Response(
            status=Status.ERROR, outcome=f"{err.__class__.__name__}: {err}"
        )
        if event.raise_on_sql_error:
            raise err
    else:
        response = Response(
            status=Status.OK, outcome=Outcome.OPERATION_SUCCESSFUL, results=results
        )
        conn.commit()
    finally:
        conn.close()
        cur.close()
    return response


def handler(event: dict, context=None):
    # Parse and validate the event
    environment = Environment.construct()
    client = boto3.client("secretsmanager")
    password = client.get_secret_value(SecretId=environment.POSTGRES_PASSWORD).get(
        "SecretString"
    )

    conn = connect_to_database(
        user=environment.POSTGRES_USERNAME,
        password=password,
        database=environment.POSTGRES_DATABASE_NAME,
        host=environment.RDS_CLUSTER_HOST,
        port=environment.RDS_CLUSTER_PORT,
    )
    if type(conn) is Response:
        response = conn
    else:
        response = Response(status=Status.OK, outcome=Outcome.OPERATION_SUCCESSFUL)

    rendered_response = response.dict(exclude_none=True)
    print(rendered_response)  # noqa: T201
    return rendered_response
