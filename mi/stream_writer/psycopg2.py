"""
Since we don't really want psycopg2 even as a local dev dependency*,
the following is here to allow tests to run without having psycopg2
installed.

* the installation process is not very consistent cross-platform,
and is probably not worth the development overhead to onboard
developers and testers
"""
try:
    import psycopg2
    from psycopg2 import errorcodes, errors, sql
    from psycopg2._psycopg import connection, cursor

    IntegrityError = errors.IntegrityError
    NOT_NULL_VIOLATION = errorcodes.NOT_NULL_VIOLATION
except ModuleNotFoundError:
    psycopg2 = None
    sql = None
    connection = None
    cursor = None
    errorcodes = None
    errors = None
    IntegrityError: type[Exception] = None
    NOT_NULL_VIOLATION = None
