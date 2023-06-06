try:
    import psycopg2
    from psycopg2 import sql
except ModuleNotFoundError:
    psycopg2 = None
    sql = None
