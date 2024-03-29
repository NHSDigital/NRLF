data "aws_lambda_invocation" "create-postgres-database-partition" {
  # Note: if database already exists then the function will fail gracefully.
  function_name = module.rds-cluster-sql-query-lambda.function_name
  input = jsonencode({
    "user" : data.aws_rds_cluster.rds-cluster.master_username
    "password" : jsondecode(data.aws_secretsmanager_secret_version.master_user_password.secret_string)["password"]
    "endpoint" : data.aws_rds_cluster.rds-cluster.endpoint
    "database_name" : data.aws_rds_cluster.rds-cluster.database_name # NB: using "default" db name to create new db
    "autocommit" : true                                              ## Required for CREATE/DROP DATABASE, don't use this anywhere else
    "sql" : {
      "statement" : (
        var.is_persistent_environment ?                                             # if is_persistent_environment
        "CREATE DATABASE {database_name};" :                                        # then create
        "DROP DATABASE IF EXISTS {database_name}; CREATE DATABASE {database_name};" # else drop and create
      )
      "identifiers" : {
        "database_name" : var.environment
      }
    }
  })

  depends_on = [
    data.aws_db_instance.rds-instance,
    module.rds-cluster-sql-query-lambda.function_name
  ]
}

data "aws_lambda_invocation" "create-schemas" {
  function_name = module.rds-cluster-sql-query-lambda.function_name
  input = jsonencode({
    "user" : data.aws_rds_cluster.rds-cluster.master_username
    "password" : jsondecode(data.aws_secretsmanager_secret_version.master_user_password.secret_string)["password"]
    "endpoint" : data.aws_rds_cluster.rds-cluster.endpoint
    "sql" : {
      "statement" : <<EOT
          CREATE SCHEMA IF NOT EXISTS fact;
          CREATE SCHEMA IF NOT EXISTS dimension;
      EOT
    }
    "raise_on_sql_error" : true
  })

  depends_on = [
    data.aws_lambda_invocation.create-postgres-database-partition,
    module.rds-cluster-sql-query-lambda.function_name
  ]
}



data "aws_lambda_invocation" "create-all-tables" {
  function_name = module.rds-cluster-sql-query-lambda.function_name
  input = jsonencode({
    "user" : data.aws_rds_cluster.rds-cluster.master_username
    "password" : jsondecode(data.aws_secretsmanager_secret_version.master_user_password.secret_string)["password"]
    "endpoint" : data.aws_rds_cluster.rds-cluster.endpoint
    "sql" : {
      "statement" : file(var.schema_path)
    }
    "raise_on_sql_error" : true
  })

  depends_on = [
    data.aws_lambda_invocation.create-schemas,
    module.rds-cluster-sql-query-lambda.function_name
  ]
}
data "aws_lambda_invocation" "create-users" {
  # Note: if users already exist then the function will fail gracefully.

  function_name = module.rds-cluster-sql-query-lambda.function_name
  input = jsonencode({
    "user" : data.aws_rds_cluster.rds-cluster.master_username
    "password" : jsondecode(data.aws_secretsmanager_secret_version.master_user_password.secret_string)["password"]
    "endpoint" : data.aws_rds_cluster.rds-cluster.endpoint
    "sql" : {
      "statement" : <<EOT
          CREATE USER {read_user} WITH PASSWORD %(read_password)s;
          CREATE USER {write_user} WITH PASSWORD %(write_password)s;
      EOT
      "identifiers" : {
        "database_name" : var.environment
        "read_user" : "${var.environment}-read"
        "write_user" : "${var.environment}-write"
      }
      "params" : {
        "read_password" : random_password.read_password.result
        "write_password" : random_password.write_password.result
      }
    }
  })
  depends_on = [
    data.aws_lambda_invocation.create-postgres-database-partition,
    module.rds-cluster-sql-query-lambda.function_name
  ]
}

data "aws_lambda_invocation" "grant-permissions" {
  # These permissions are tested in associated integration tests

  function_name = module.rds-cluster-sql-query-lambda.function_name
  input = jsonencode({
    "user" : data.aws_rds_cluster.rds-cluster.master_username
    "password" : jsondecode(data.aws_secretsmanager_secret_version.master_user_password.secret_string)["password"]
    "endpoint" : data.aws_rds_cluster.rds-cluster.endpoint
    "sql" : {
      "statement" : <<EOT
        GRANT CONNECT ON DATABASE {database_name} TO {read_user};
        GRANT USAGE ON SCHEMA fact TO {read_user};
        GRANT USAGE ON SCHEMA dimension TO {read_user};
        GRANT SELECT ON ALL TABLES IN SCHEMA fact TO {read_user};
        GRANT SELECT ON ALL TABLES IN SCHEMA dimension TO {read_user};

        GRANT CONNECT ON DATABASE {database_name} TO {write_user};
        GRANT USAGE ON SCHEMA fact TO {write_user};
        GRANT USAGE ON SCHEMA dimension TO {write_user};
        GRANT USAGE ON ALL SEQUENCES IN SCHEMA dimension TO {write_user};
        GRANT SELECT ON ALL TABLES IN SCHEMA fact TO {write_user};
        GRANT SELECT ON ALL TABLES IN SCHEMA dimension TO {write_user};
        GRANT SELECT ON ALL SEQUENCES IN SCHEMA dimension TO {write_user};
        GRANT INSERT ON ALL TABLES IN SCHEMA fact TO {write_user};
        GRANT INSERT ON ALL TABLES IN SCHEMA dimension TO {write_user};
        GRANT UPDATE ON ALL TABLES IN SCHEMA fact TO {write_user};
        GRANT UPDATE ON ALL TABLES IN SCHEMA dimension TO {write_user};
        GRANT UPDATE ON ALL SEQUENCES IN SCHEMA dimension TO {write_user};
      EOT
      "identifiers" : {
        "database_name" : var.environment
        "read_user" : "${var.environment}-read"
        "write_user" : "${var.environment}-write"
      }
    }
    "raise_on_sql_error" : true
  })

  depends_on = [
    data.aws_lambda_invocation.create-users,
    data.aws_lambda_invocation.create-all-tables,
    module.rds-cluster-sql-query-lambda.function_name
  ]
}

data "aws_lambda_invocation" "set-static-dimensions-data" {
  function_name = module.rds-cluster-sql-query-lambda.function_name
  input = jsonencode({
    "user" : "${var.environment}-write"
    "password" : random_password.write_password.result
    "endpoint" : data.aws_rds_cluster.rds-cluster.endpoint
    "sql" : {
      "statement" : file(var.static_dimensions_path)
    }
    "raise_on_sql_error" : true
  })

  depends_on = [
    data.aws_lambda_invocation.create-users,
    data.aws_lambda_invocation.create-all-tables,
    data.aws_lambda_invocation.grant-permissions,
    module.rds-cluster-sql-query-lambda.function_name
  ]
}
