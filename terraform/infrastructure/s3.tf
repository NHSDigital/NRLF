resource "aws_s3_bucket_policy" "allow-lambda-to-read" {
  bucket = local.auth_store_id
  policy = data.aws_iam_policy_document.allow-authorizer-lambda-to-read.json
}

data "aws_iam_policy_document" "allow-authorizer-lambda-to-read" {
  statement {
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::${local.aws_account_id}:role/${module.consumer__readDocumentReference.lambda_role_name}",
        "arn:aws:iam::${local.aws_account_id}:role/${module.consumer__countDocumentReference.lambda_role_name}",
        "arn:aws:iam::${local.aws_account_id}:role/${module.consumer__searchDocumentReference.lambda_role_name}",
        "arn:aws:iam::${local.aws_account_id}:role/${module.consumer__searchPostDocumentReference.lambda_role_name}",
        "arn:aws:iam::${local.aws_account_id}:role/${module.producer__createDocumentReference.lambda_role_name}",
        "arn:aws:iam::${local.aws_account_id}:role/${module.producer__deleteDocumentReference.lambda_role_name}",
        "arn:aws:iam::${local.aws_account_id}:role/${module.producer__readDocumentReference.lambda_role_name}",
        "arn:aws:iam::${local.aws_account_id}:role/${module.producer__searchDocumentReference.lambda_role_name}",
        "arn:aws:iam::${local.aws_account_id}:role/${module.producer__searchPostDocumentReference.lambda_role_name}",
        "arn:aws:iam::${local.aws_account_id}:role/${module.producer__updateDocumentReference.lambda_role_name}",
        "arn:aws:iam::${local.aws_account_id}:role/${module.producer__upsertDocumentReference.lambda_role_name}",
      ]
    }

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]

    resources = [
      local.auth_store_arn,
      "${local.auth_store_arn}/*",
    ]
  }
}
