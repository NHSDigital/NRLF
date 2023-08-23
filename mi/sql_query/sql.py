from mi.sql_query.model import Sql
from mi.sql_query.psycopg2 import connection as Connection
from mi.sql_query.psycopg2 import cursor as Cursor
from mi.sql_query.psycopg2 import sql as psycopg2_sql

STATEMENT_SEPARATOR = ";"
SELECT = "SELECT"


def _is_select_query(query: str):
    return query.startswith(SELECT)


def execute_sql_query(cursor: Cursor, sql: Sql) -> list:
    connection: Connection = cursor.connection

    # Need to split statements up since when using "autocommit"
    # it is not possible to invoke multiple statements in a single call.
    # In practice this is needed for the database clear-down in the
    # database_administration.tf
    statements: list[str] = (
        filter(
            str.strip,
            sql.statement.split(STATEMENT_SEPARATOR),
        )
        if connection.autocommit
        else [sql.statement]  # when not "autocommit" can just run in one call
    )
    for stmt in statements:
        query = psycopg2_sql.SQL(stmt).format(
            **{k: psycopg2_sql.Identifier(v) for k, v in sql.identifiers.items()}
        )
        cursor.execute(query, vars=sql.params)
    return cursor.fetchall() if _is_select_query(sql.statement) else None
