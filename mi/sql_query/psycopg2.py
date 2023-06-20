try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2._psycopg import connection
except ModuleNotFoundError:
    psycopg2 = None
    sql = None
    connection = None
