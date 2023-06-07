resource "aws_iam_role" "terraform_role" {
  name = "NHSDTerraformRole"
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

module "terraform_role_acm" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--terraform-acm-certificates"
  role_name = aws_iam_role.terraform_role.name
  iam_permissions = [
    {
      Action = [
        "acm:DeleteCertificate",
        "acm:DescribeCertificate",
        "acm:ListTagsForCertificate",
        "acm:RequestCertificate"
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:acm:us-east-1:${data.aws_caller_identity.current.account_id}:certificate/*"
      ]
    }
  ]
}

module "terraform_role_apigateway" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--terraform-api-gateway"
  role_name = aws_iam_role.terraform_role.name
  iam_permissions = [
    {
      # APIs
      Action = [
        "apigateway:CreateRestApi",
        "apigateway:DeleteRestApi",
        "apigateway:GetRestApi",
        "apigateway:PutRestApi",
        "apigateway:UpdateRestApi",
      ],
      Effect = "Allow"
      Resource = [
        "arn:aws:apigateway:${data.aws_caller_identity.current.account_id}::${local.region}/apis/${local.project}--*"
      ]
    },
    # BasePathMapping
    {
      Action = [
        "apigateway:CreateBasePathMapping",
        "apigateway:DeleteBasePathMapping",
        "apigateway:GetBasePathMapping",
      ],
      Effect = "Allow"
      Resource = [
        "arn:aws:apigateway:${local.region}::/domainnames/*/basepathmappings/*"
      ]
    },

    # DomainName
    {
      Action = [
        "apigateway:CreateDomainName",
        "apigateway:DeleteDomainName",
        "apigateway:GetDomainName",
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:apigateway:${local.region}::/domainnames/*"
      ]
    },
    # Deployment
    {
      Action = [
        "apigateway:CreateDeployment",
        "apigateway:DeleteDeployment",
        "apigateway:GetDeployment",
      ],
      Effect = "Allow",
      Resource = [
        "arn:aws:apigateway:${local.region}::/apis/${local.project}--*/deployments/*"
      ]
    },
    # GatewayResponse
    {
      Action = [
        "apigateway:DeleteGatewayResponse",
        "apigateway:GetGatewayResponse",
        "apigateway:PutGatewayResponse",
      ],
      Effect = "Allow"
      Resource = [
        "arn:aws:apigateway:${local.region}::/restapis/${local.project}--*/gatewayresponses/*"
      ]
    },
    # Stages
    {
      Action = [
        "apigateway:CreateStage",
        "apigateway:DeleteStage",
        "apigateway:GetStage",
        "apigateway:UpdateStage",
      ],
      Effect = "Allow",
      Resource = [
        "arn:aws:apigateway:${local.region}::/apis/${local.project}--*/stages/*"
      ]
    },
    # Resources
    {
      Action = [
        "apigateway:GetResources",
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:apigateway:${local.region}::/restapis/${local.project}--*/resources"
      ]
    }
  ]
}

module "terraform_role_dynamodb" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--terraform-dynamodb"
  role_name = aws_iam_role.terraform_role.name
  iam_permissions = [
    {
      # Table Operations
      Action = [
        "dynamodb:CreateTable",
        "dynamodb:DeleteTable",
        "dynamodb:DescribeTable"
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:dynamodb:${local.region}:${data.aws_caller_identity.current.account_id}:table/${local.project}--*"
      ]
    },
    {
      # CRUD Operations - TODO: Scope to each table
      Action = [
        "dynamodb:DeleteItem",
        "dynamodb:GetItem",
        "dynamodb:ListTagsOfResource",
        "dynamodb:PutItem",
        "dynamodb:DescribeContinuousBackups",
        "dynamodb:DescribeTimeToLive",
        "dynamodb:UpdateContinuousBackups",
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:dynamodb:${local.region}:${data.aws_caller_identity.current.account_id}:table/${local.project}--*"
      ]
    }
  ]
}

module "terraform_role_firehose" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--terraform-firehose"
  role_name = aws_iam_role.terraform_role.name
  iam_permissions = [
    {
      Action = [
        "firehose:CreateDeliveryStream",
        "firehose:DeleteDeliveryStream",
        "firehose:DescribeDeliveryStream",
        "firehose:ListTagsForDeliveryStream",
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:firehose:${local.region}:${data.aws_caller_identity.current.account_id}:deliverystream/${local.project}--*"
      ]
    }
  ]
}


module "terraform_role_iam" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--terraform-iam"
  role_name = aws_iam_role.terraform_role.name
  iam_permissions = [
    {
      # Roles
      Action = [
        "iam:CreateRole",
        "iam:CreateServiceLinkedRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:PassRole",
        "iam:ListInstanceProfilesForRole",
        "iam:ListAttachedRolePolicies",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy"
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${local.project}--*"
      ]
    },
    {
      # Policies
      Action = [
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies",
        "iam:PutRolePolicy",
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${local.project}--*"
      ]
    }
  ]
}

module "terraform_role_kms" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--terraform-kms"
  role_name = aws_iam_role.terraform_role.name
  iam_permissions = [
    # Keys
    {
      Action = [
        "kms:CreateKey",
        "kms:DescribeKey",
        "kms:GetKeyPolicy",
        "kms:GetKeyRotationStatus",
        "kms:ListResourceTags",
        "kms:PutKeyPolicy",
        "kms:ScheduleKeyDeletion",
        "kms:TagResource",
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:kms:${local.region}:${data.aws_caller_identity.current.account_id}:key/*"
      ]
    },
    {
      Action = [
        "kms:CreateAlias",
        "kms:DeleteAlias",
        "kms:ListAliases",
        "kms:ListResourceTags",
        "kms:TagResource",
      ]
      Effect   = "Allow"
      Resource = ["arn:aws:kms:${local.region}:${data.aws_caller_identity.current.account_id}:alias/*"]
    }
  ]
}

module "terraform_role_lambda" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--terraform-lambda"
  role_name = aws_iam_role.terraform_role.name
  iam_permissions = [
    {
      Action = [
        "lambda:AddPermission",
        "lambda:DeleteLayerVersion",
        "lambda:GetLayerVersion",
        "lambda:GetPolicy",
        "lambda:PublishLayerVersion",
        "lambda:RemovePermission",
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:lambda:${local.region}:${data.aws_caller_identity.current.account_id}:function:${local.project}--*",
        "arn:aws:lambda:${local.region}:${data.aws_caller_identity.current.account_id}:layer:${local.project}--*"
      ]
    }
  ]
}

module "terraform_role_cloudwatch" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--terraform-cloudwatch"
  role_name = aws_iam_role.terraform_role.name
  iam_permissions = [
    {
      # Log Groups
      Action = [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups",
        "logs:ListTagsLogGroup",
        "logs:PutRetentionPolicy",
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:logs:${local.region}:${data.aws_caller_identity.current.account_id}:log-group:${local.project}--*",
        "arn:aws:logs:${local.region}:${data.aws_caller_identity.current.account_id}:log-group:${local.project}--*:*"
      ]
    },
    {
      # Log Streams
      Action = [
        "logs:CreateLogStream",
        "logs:DeleteLogStream",
        "logs:DescribeLogStreams",
      ]
      Effect   = "Allow"
      Resource = ["arn:aws:logs:${local.region}:${data.aws_caller_identity.current.account_id}:log-group:${local.project}--*:log-stream:*"]
    },
    {
      # Subscription Filters
      Action = [
        "logs:DeleteSubscriptionFilter",
        "logs:DescribeSubscriptionFilters",
        "logs:PutSubscriptionFilter",
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:logs:${local.region}:${data.aws_caller_identity.current.account_id}:log-group:${local.project}--*",
        "arn:aws:logs:${local.region}:${data.aws_caller_identity.current.account_id}:log-group:${local.project}--*:*",
        "arn:aws:logs:${local.region}:${data.aws_caller_identity.current.account_id}:log-group:${local.project}--*:log-stream:*"
      ]
    }
  ]
}

module "terraform_role_route53" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--terraform-route53"
  role_name = aws_iam_role.terraform_role.name
  iam_permissions = [
    {
      # Hosted Zone
      Action = [
        "route53:ChangeResourceRecordSets",
        "route53:GetChange",
        "route53:GetHostedZone",
        "route53:ListHostedZones",
        "route53:ListResourceRecordSets",
        "route53:ListTagsForResource",
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:route53:::hostedzone/${aws_route53_zone.dev-ns.id}",
        "arn:aws:route53:::change/*",
      ]
    }
  ]
}

module "terraform_role_s3" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--terraform-s3"
  role_name = aws_iam_role.terraform_role.name
  iam_permissions = [
    {
      # Bucket Operations
      Action = [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:GetAccelerateConfiguration",
        "s3:GetBucketAcl",
        "s3:GetBucketCORS",
        "s3:GetBucketLogging",
        "s3:GetBucketNotification",
        "s3:GetBucketObjectLockConfiguration",
        "s3:GetBucketPolicy",
        "s3:GetBucketRequestPayment",
        "s3:GetBucketTagging",
        "s3:GetBucketVersioning",
        "s3:GetBucketWebsite",
        "s3:GetEncryptionConfiguration",
        "s3:GetLifecycleConfiguration",
        "s3:GetReplicationConfiguration",
        "s3:ListBucket",
        "s3:ListBucketVersions",
        "s3:PutBucketNotification",
        "s3:PutBucketTagging",
        "s3:PutBucketVersioning",
        "s3:PutEncryptionConfiguration",
        "s3:PutLifecycleConfiguration",
      ]
      Effect = "Allow"
      Resource = [
        "arn:aws:s3:::${local.project}--*"
      ]
    },
    {
      # Object Operations
      Action = [
        "s3:DeleteObject",
        "s3:GetObject",
        "s3:GetObjectTagging",
        "s3:GetObjectVersion",
        "s3:PutObject"
      ]
      Effect   = "Allow"
      Resource = ["arn:aws:s3:::${local.project}--*/*"]
    }
  ]
}


module "terraform_role_secretsmanager" {
  source    = "../modules/role-policy"
  name      = "${local.prefix}--terraform-secretsmanager"
  role_name = aws_iam_role.terraform_role.name
  iam_permissions = [
    {
      Action = [
        "secretsmanager:CreateSecret",
        "secretsmanager:DeleteSecret",
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetResourcePolicy",
        "secretsmanager:GetSecretValue"
      ]
      Effect   = "Allow"
      Resource = ["arn:aws:secretsmanager:${local.region}:${data.aws_caller_identity.current.account_id}:secret:${local.project}--*"]
    }
  ]
}
