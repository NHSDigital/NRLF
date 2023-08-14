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

module "rds-cluster-stream-writer" {
  source      = "../lambda"
  parent_path = var.name
  name        = "stream_writer"
  region      = var.region
  prefix      = var.prefix
  kms_key_id  = var.cloudwatch_kms_arn
  environment_variables = {
    POSTGRES_DATABASE_NAME = var.environment
    RDS_CLUSTER_HOST       = data.aws_rds_cluster.rds-cluster.reader_endpoint
    RDS_CLUSTER_PORT       = data.aws_rds_cluster.rds-cluster.port
    POSTGRES_USERNAME      = "${var.environment}-write"
    POSTGRES_PASSWORD      = aws_secretsmanager_secret.write_password.arn
  }
  layers = concat(var.layers, [module.psycopg2.layer_arn, module.nrlf.layer_arn, module.lambda_utils.layer_arn])
  additional_policies = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    aws_iam_policy.stream-writer-lambda.arn
  ]
  handler = "${var.name}.stream_writer.index.handler"
  depends_on = [
    data.aws_rds_cluster.rds-cluster,
    aws_iam_policy.stream-writer-lambda
  ]
  vpc = {
    subnet_ids         = data.aws_subnets.rds-cluster-vpc-private-subnets.ids
    security_group_ids = [data.aws_security_group.rds-cluster-vpc-security-group.id]
  }
}

resource "aws_iam_policy" "stream-writer-lambda" {
  name        = "${var.prefix}-stream-writer-lambda"
  description = "Read write password from secretsmanager"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Effect = "Allow"
        Resource = [
          aws_secretsmanager_secret.write_password.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:DescribeStream",
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:ListStreams"
        ],
        Resource = [
          var.dynamodb_table.stream_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt"
        ],
        Resource = [
          var.dynamodb_table_kms_key_arn
        ]
      }
    ]
  })
}
