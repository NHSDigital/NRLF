resource "aws_iam_role" "developer_role" {
  name = "NHSDDeveloperRole"
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

module "developer_role_tf_state" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--developer-tf-state"
  role_name = aws_iam_role.developer_role.name
  iam_permissions = [
    {
      Action = [
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetObject",
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:DeleteItem",
        "s3:ListBucket"
      ]
      Effect = "Allow"
      Resource = [
        data.aws_dynamodb_table.terraform_state_lock.arn,
        data.aws_s3_bucket.terraform_state.arn,
        "${data.aws_s3_bucket.terraform_state.arn}/*"
      ]
    }
  ]
}

module "developer_role_deny_pe_tf_state" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--developer-deny-pe-tf-state"
  role_name = aws_iam_role.developer_role.name
  iam_permissions = [
    {
      Action = [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ]
      Effect = "Deny"
      Resource = [
        "${data.aws_s3_bucket.terraform_state.arn}/${local.project}/prod/*",
        "${data.aws_s3_bucket.terraform_state.arn}/${local.project}/test/*",
        "${data.aws_s3_bucket.terraform_state.arn}/${local.project}/ref/*",
        "${data.aws_s3_bucket.terraform_state.arn}/${local.project}/mgmt/*",
        "${data.aws_s3_bucket.terraform_state.arn}/${local.project}/dev/terraform-state-infrastructure"
      ]
    },
    {
      Action = [
        "s3:DeleteObject"
      ]
      Effect = "Deny"
      Resource = [
        "${data.aws_s3_bucket.terraform_state.arn}/${local.project}/dev/*"
      ]
    }
  ]
}

module "developer_role_assume_tf_role" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--developer-assume-tf-role"
  role_name = aws_iam_role.developer_role.name
  iam_permissions = [
    {
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Resource = [
        "arn:aws:iam::${data.aws_secretsmanager_secret_version.dev_account_id.secret_string}:role/terraform",
      ]
    }
  ]
}

module "developer_role_read_account_id" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--developer-read-account-id"
  role_name = aws_iam_role.developer_role.name
  iam_permissions = [
    {
      Action = [
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:ListSecretVersionIds"
      ]
      Effect = "Allow"
      Resource = [
        data.aws_secretsmanager_secret.dev_account_id.arn
      ]
    }
  ]
}


module "developer_role_read_tf_log" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--developer-read-ci-logs"
  role_name = aws_iam_role.developer_role.name
  iam_permissions = [
    {
      Action = [
        "s3:ListAllMyBuckets"
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:s3:::*"
      ]
    },
    {
      Action = [
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Effect = "Allow"
      Resource = [
        data.aws_s3_bucket.ci_logging.arn,
        "${data.aws_s3_bucket.ci_logging.arn}/*"
      ]
    }
  ]
}

module "developer_role_read_truststore" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--developer-read-truststore"
  role_name = aws_iam_role.developer_role.name
  iam_permissions = [
    {
      Action = [
        "s3:GetObject"
      ]
      Effect = "Allow"
      Resource = [
        "${data.aws_s3_bucket.truststore.arn}/*"
      ]
    }
  ]
}
