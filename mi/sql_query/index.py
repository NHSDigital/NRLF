from typing import Union

from mi.sql_query.model import Environment, Outcome, Response, SqlQueryEvent, Status
from mi.sql_query.psycopg2 import connection, psycopg2
from mi.sql_query.sql import execute_sql_query


def connect_to_database(
    raise_on_error=False, autocommit=False, **connect_kwargs
) -> Union[connection, Response]:
    try:
        conn = psycopg2.connect(**connect_kwargs)
        conn.autocommit = autocommit
        return conn
    except Exception as err:
        response = Response(
            status=Status.ERROR, outcome=f"{err.__class__.__name__}: {err}"
        )
        if raise_on_error:
            raise err
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
    _event = SqlQueryEvent(**event)
    environment = Environment.construct()

    conn = connect_to_database(
        user=_event.user.get_secret_value(),
        password=_event.password.get_secret_value(),
        database=_event.database_name or environment.POSTGRES_DATABASE_NAME,
        host=_event.endpoint or environment.RDS_CLUSTER_HOST,
        port=environment.RDS_CLUSTER_PORT,
        raise_on_error=_event.raise_on_sql_error,
        autocommit=_event.autocommit,
    )
    if type(conn) is Response:
        response = conn
    else:
        response = execute_sql(conn=conn, event=_event)

    rendered_response = response.dict(exclude_none=True)
    print(rendered_response)  # noqa: T201
    return rendered_response
