from mi.schema_lambda.model import Environment, Outcome, QueryEvent, Response, Status
from mi.schema_lambda.psycopg2 import psycopg2, sql


def _is_select_query(query: str):
    return query.startswith("SELECT")


def handler(event: dict, context=None):
    query_event = QueryEvent(**event)
    environment = Environment.construct()
    conn = psycopg2.connect(
        user=query_event.user.get_secret_value(),
        password=query_event.password.get_secret_value(),
        database=environment.RDS_CLUSTER_DATABASE_NAME,
        host=query_event.endpoint or environment.RDS_CLUSTER_PORT,
        port=environment.RDS_CLUSTER_PORT,
    )

    cur = conn.cursor()
    try:
        query = sql.SQL(query_event.query.statement).format(
            **{k: sql.Identifier(v) for k, v in query_event.query.identifiers.items()}
        )
        cur.execute(query, vars=query_event.query.params)
    except Exception as err:
        response = Response(
            status=Status.ERROR, outcome=f"{err.__class__.__name__}: {err}"
        )
    else:
        response = Response(
            status=Status.OK,
            outcome=Outcome.OPERATION_SUCCESSFUL.value,
            results=cur.fetchall()
            if _is_select_query(query_event.query.statement)
            else None,
        )
        conn.commit()
    finally:
        conn.close()
        cur.close()

    rendered_response = response.dict(exclude_none=True)
    print(rendered_response)  # noqa: T201
    return rendered_response
