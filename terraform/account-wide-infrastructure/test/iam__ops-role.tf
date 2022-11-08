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


module "ops_role_permissions" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--ops-permissions"
  role_name = aws_iam_role.ops_role.name
  iam_permissions = [
    {
      Action = [
        "acm:Describe*",
        "acm:Get*",
        "acm:List*",
        "cloudwatch:*",
        "dynamodb:*",
        "firehose:Describe*",
        "firehose:List*",
        "glue:*",
        "iam:Generate*",
        "iam:Get*",
        "iam:List*",
        "iam:Simulate*",
        "kinesis:Describe*",
        "kinesis:Get*",
        "kinesis:List*",
        "kms:*",
        "lambda:*",
        "logs:*",
        "route53:Get*",
        "route53:List*",
        "route53:Test*",
        "s3:*",
        "secretsmanager:*",
        "sns:*",
        "sqs:*",
        "ssm:*",
        "tag:*",
        "apigateway:*"
      ]
      Effect = "Allow"
      Resource = [
        "*"
      ]
    }
  ]
}
