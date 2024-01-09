resource "aws_s3_bucket" "firehose" {
  bucket        = "${var.prefix}-firehose"
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "firehose" {
  bucket = aws_s3_bucket.firehose.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.firehose.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_policy" "firehose-policy" {
  bucket = aws_s3_bucket.firehose.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "firehose-policy"
    Statement = [
      {
        Sid       = "HTTPSOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.firehose.arn,
          "${aws_s3_bucket.firehose.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
    ]
  })
}

resource "aws_s3_bucket_public_access_block" "firehose-public-access-block" {
  bucket = aws_s3_bucket.firehose.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "firehose" {
  bucket = aws_s3_bucket.firehose.id

  rule {
    id     = "FirehoseLifecycle"
    status = "Enabled"

    transition {
      days          = local.s3.transition_storage.infrequent_access.days
      storage_class = local.s3.transition_storage.infrequent_access.storage_class
    }
    transition {
      days          = local.s3.transition_storage.glacier.days
      storage_class = local.s3.transition_storage.glacier.storage_class
    }
    expiration {
      days = local.s3.expiration.days
    }
  }
}

resource "aws_s3_bucket_versioning" "firehose" {
  bucket = aws_s3_bucket.firehose.id
  versioning_configuration {
    status = var.is_persistent_environment ? "Enabled" : "Disabled"
  }
}



resource "aws_iam_policy" "firehose-alert--s3-read" {
  name        = "${var.prefix}--firehose-alert--s3-read"
  description = "Read errors files from the Firehose S3 bucket"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Effect = "Allow"
        Resource = [
          aws_kms_key.firehose.arn
        ]
      },
      {
        Action = [
          "s3:GetObject"
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.firehose.arn}/${var.error_prefix}/*"
        ]
      }
    ]
  })
}
