module "rds-cluster-schema-lambda" {
  source      = "../lambda"
  parent_path = var.name
  name        = "schema_lambda"
  region      = var.region
  prefix      = var.prefix
  kms_key_id  = var.cloudwatch_kms_arn
  environment_variables = {
    RDS_CLUSTER_DATABASE_NAME = data.aws_rds_cluster.rds-cluster.database_name
    RDS_CLUSTER_HOST          = data.aws_rds_cluster.rds-cluster.reader_endpoint
    RDS_CLUSTER_PORT          = data.aws_rds_cluster.rds-cluster.port
  }
  layers              = concat(var.layers, [module.psycopg2.layer_arn])
  additional_policies = ["arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"]
  handler             = "${var.name}.schema_lambda.handler.handler"
  depends_on = [
    data.aws_rds_cluster.rds-cluster
  ]
  vpc = {
    subnet_ids         = data.aws_subnets.rds-cluster-vpc-private-subnets.ids
    security_group_ids = [data.aws_security_group.rds-cluster-vpc-security-group.id]
  }
}


data "aws_lambda_invocation" "rds-cluster-schema-creation" {
  function_name = module.rds-cluster-schema-lambda.function_name
  input = jsonencode({
    "user" : data.aws_rds_cluster.rds-cluster.master_username
    "password" : jsondecode(data.aws_secretsmanager_secret_version.master_user_password.secret_string)["password"]
    "endpoint" : data.aws_rds_cluster.rds-cluster.endpoint
    "query" : {
      "statement" : file(var.create_sql_path)
      "identifiers" : {
        "table_name" : "${var.prefix}-${var.name}"
        "database_name" : data.aws_rds_cluster.rds-cluster.database_name
        "read_user" : "${var.prefix}-${var.name}-read"
        "write_user" : "${var.prefix}-${var.name}-write"
      }
      "params" : {
        "read_password" : random_password.read_password.result
        "write_password" : random_password.write_password.result
      }
    }
  })
  depends_on = [
    data.aws_db_instance.rds-instance,
    module.rds-cluster-schema-lambda
  ]
}
