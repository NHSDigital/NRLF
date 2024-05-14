resource "aws_s3_bucket" "authorization-store" {
  bucket        = "${local.prefix}--authorization-store"
  force_destroy = true

  tags = {
    Name        = "authorization store"
    Environment = "${local.prefix}"
  }
}

resource "aws_s3_bucket_public_access_block" "authorization-store-public-access-block" {
  bucket = aws_s3_bucket.authorization-store.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "authorization-store" {
  bucket = aws_s3_bucket.authorization-store.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "authorization-store" {
  bucket = aws_s3_bucket.authorization-store.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_policy" "allow-lambda-to-read" {
  bucket = aws_s3_bucket.authorization-store.id
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
      aws_s3_bucket.authorization-store.arn,
      "${aws_s3_bucket.authorization-store.arn}/*",
    ]
  }
}

resource "aws_iam_policy" "read-authorization-store-s3" {
  name        = "${local.prefix}--read-authorization-store-s3"
  description = "Read the authorization store S3 bucket"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Effect = "Allow"
        Resource = [
          aws_s3_bucket.authorization-store.arn
        ]
      },
    ]
  })
}
