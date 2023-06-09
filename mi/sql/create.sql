-- First time create (empty, with migration applied after)
CREATE TABLE IF NOT EXISTS {table_name};

-- Drop and recreate READ user
DROP USER IF EXISTS {read_user};
CREATE USER {read_user} WITH PASSWORD %(read_password)s;
GRANT CONNECT ON DATABASE {database_name} TO {read_user};
GRANT USAGE ON SCHEMA public TO {read_user};
GRANT SELECT ON {table_name} TO {read_user};

-- Drop and recreate WRITE user
DROP USER IF EXISTS {write_user};
CREATE USER {write_user} WITH PASSWORD %(write_password)s;
GRANT CONNECT ON DATABASE {database_name} TO {write_user};
GRANT USAGE ON SCHEMA public TO {write_user};
GRANT INSERT ON {table_name} TO {write_user};
