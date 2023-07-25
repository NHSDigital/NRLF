from mi.stream_writer.model import Sql
from mi.stream_writer.psycopg2 import sql as psycopg2_sql


def _is_select_query(query: str):
    return query.startswith("SELECT")


def execute_sql_query(cursor, sql: Sql) -> list:
    query = psycopg2_sql.SQL(sql.statement).format(
        **{k: psycopg2_sql.Identifier(v) for k, v in sql.identifiers.items()}
    )
    cursor.execute(query, vars=sql.params)
    return cursor.fetchall() if _is_select_query(sql.statement) else None
