resource "aws_s3_bucket" "mi-errors" {
  bucket        = "${var.prefix}-mi-errors"
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mi-errors" {
  bucket = aws_s3_bucket.mi-errors.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.mi-errors.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "mi-errors" {
  bucket = aws_s3_bucket.mi-errors.id

  rule {
    id     = "MiErrorsLifecycle"
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

resource "aws_s3_bucket_versioning" "mi-errors" {
  bucket = aws_s3_bucket.mi-errors.id
  versioning_configuration {
    status = var.is_persistent_environment ? "Enabled" : "Disabled"
  }
}



resource "aws_iam_policy" "mi-errors-alert--s3-read" {
  name        = "${var.prefix}--mi-errors-alert--s3-read"
  description = "Read error files from the mi errors S3 bucket"
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
          aws_kms_key.mi-errors.arn
        ]
      },
      {
        Action = [
          "s3:GetObject"
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.mi-errors.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_kms_key" "mi-errors" {
}

resource "aws_kms_alias" "mi-errors" {
  name          = "alias/${var.prefix}-mi-errors"
  target_key_id = aws_kms_key.mi-errors.key_id
}
