resource "aws_iam_role" "ops_role" {
  name = "NHSDOpsRole"
  assume_role_policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Action : "sts:AssumeRole",
        Principal : {
          AWS : "arn:aws:iam::${data.aws_secretsmanager_secret_version.identities_account_id.secret_string}:root"
        },
        Effect : "Allow"
      }
    ]
  })
}


module "ops_role_read_only_resources" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--ops-read-only"
  role_name = aws_iam_role.ops_role.name
  iam_permissions = [
    {
      Action = [
        "acm:Describe*",
        "acm:Get*",
        "acm:List*",
        "cloudwatch:Describe*",
        "cloudwatch:Get*",
        "cloudwatch:List*",
        "dynamodb:BatchGet*",
        "dynamodb:Describe*",
        "dynamodb:Get*",
        "dynamodb:List*",
        "dynamodb:Query",
        "dynamodb:Scan",
        "events:Describe*",
        "events:List*",
        "events:Test*",
        "firehose:Describe*",
        "firehose:List*",
        "iam:Generate*",
        "iam:Get*",
        "iam:List*",
        "iam:Simulate*",
        "kinesis:Describe*",
        "kinesis:Get*",
        "kinesis:List*",
        "logs:Describe*",
        "logs:Get*",
        "logs:FilterLogEvents",
        "logs:ListTagsLogGroup",
        "logs:TestMetricFilter",
        "rds:Describe*",
        "rds:List*",
        "rds:Download*",
        "route53:Get*",
        "route53:List*",
        "route53:Test*",
        "secretsmanager:List*",
        "secretsmanager:Describe*",
        "secretsmanager:GetResourcePolicy",
        "sns:Get*",
        "sns:List*",
        "sns:Check*",
        "ssm:Describe*",
        "ssm:Get*",
        "ssm:List*",
        "tag:Get*",
        "apigateway:GET*"
      ]
      Effect = "Allow"
      Resource = [
        "*"
      ]
    },
    {
      Action = [
        "s3:Get*",
        "s3:List*",
        "s3:Head*"
      ]
      Effect = "Allow"
      Resource = [
        "*"
      ]
    },
    {
      Action = [
        "kms:Describe*",
        "kms:Get*",
        "kms:List*",
        "kms:GenerateDataKey*",
        "kms:Encrypt",
        "kms:ReEncrypt*",
        "kms:Decrypt",
      ]
      Effect = "Allow"
      Resource = [
        "*"
      ]
    },
    {
      Action = [
        "sqs:Get*",
        "sqs:List*",
      ]
      Effect = "Allow"
      Resource = [
        "*"
      ]
    },
    {
      Action = [
        "glue:Get*",
        "glue:List*",
        "glue:BatchGet*"
      ]
      Effect = "Allow"
      Resource = [
        "*"
      ]
    },
    {
      Action = [
        "lambda:List*",
        "lambda:Get*"
      ]
      Effect = "Allow"
      Resource = [
        "*"
      ]
    }
  ]
}
