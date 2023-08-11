import traceback
from dataclasses import asdict
from functools import partial, wraps
from typing import Callable, TypeVar

T = TypeVar("T", bound=Callable[..., any])

from mi.stream_writer.model import (
    DIMENSION_TYPES,
    Dimension,
    ErrorResponse,
    GoodResponse,
    RecordParams,
)
from mi.stream_writer.psycopg2 import connection as Connection
from mi.stream_writer.psycopg2 import cursor as Cursor
from mi.stream_writer.psycopg2 import errorcodes, errors
from mi.stream_writer.psycopg2 import sql as psycopg2_sql


def catch_error(log_fields: list[str] = None) -> Callable[[T], T]:
    if log_fields is None:
        log_fields = []

    def decorator(fn: T) -> T:
        @wraps(fn)
        def wrapper(*args: tuple[any, ...], **kwargs: any) -> any:
            try:
                return fn(*args, **kwargs)
            except Exception as error:
                metadata = {k: v for k, v in kwargs.items() if k in log_fields}
                return ErrorResponse(
                    error=str(error),
                    error_type=error.__class__.__name__,
                    function=f"{fn.__module__}.{fn.__name__}",
                    trace=traceback.format_exc(),
                    metadata=metadata,
                )

        return wrapper

    return decorator


def _execute_sql(
    cursor: Cursor, statement: str, params: dict, identifiers: dict = None
):
    query = psycopg2_sql.SQL(statement)
    if identifiers:
        query = query.format(
            **{k: psycopg2_sql.Identifier(v) for k, v in identifiers.items()}
        )
    try:
        cursor.execute(query, vars=params)
    except:
        connection: Connection = cursor.connection
        connection.rollback()
        raise


@catch_error(log_fields=["document_pointer"])
def insert_mi_record(
    record: RecordParams,
    sql: str,
    cursor: Cursor,
    dimension_types: tuple[type[Dimension]] = DIMENSION_TYPES,
    integrity_error_type: type[errors.IntegrityError] = errors.IntegrityError,
) -> GoodResponse:
    insert_record = partial(
        _execute_sql, cursor=cursor, statement=sql, params=asdict(record)
    )
    # Try to insert the Fact
    try:
        insert_record()
    except integrity_error_type as error:
        if error.pgcode != errorcodes.NOT_NULL_VIOLATION:
            raise error
    else:
        return GoodResponse()

    # On NOT NULL CONSTRAINT, insert Dimensions first
    for dimension_type in dimension_types:
        dim = record.to_dimension(dimension_type=dimension_type)
        _execute_sql(cursor=cursor, statement=dim.sql, params=asdict(dim))
    insert_record()
    return GoodResponse()
