module "rds-cluster-sql-query-lambda" {
  source      = "../lambda"
  parent_path = var.name
  name        = "sql_query"
  region      = var.region
  prefix      = var.prefix
  kms_key_id  = var.cloudwatch_kms_arn
  environment_variables = {
    POSTGRES_DATABASE_NAME = var.environment
    RDS_CLUSTER_HOST       = data.aws_rds_cluster.rds-cluster.reader_endpoint
    RDS_CLUSTER_PORT       = data.aws_rds_cluster.rds-cluster.port
  }
  layers              = concat(var.layers, [module.psycopg2.layer_arn])
  additional_policies = ["arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"]
  handler             = "${var.name}.sql_query.index.handler"
  depends_on = [
    data.aws_rds_cluster.rds-cluster
  ]
  vpc = {
    subnet_ids         = data.aws_subnets.rds-cluster-vpc-private-subnets.ids
    security_group_ids = [data.aws_security_group.rds-cluster-vpc-security-group.id]
  }
}
