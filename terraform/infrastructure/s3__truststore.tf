resource "aws_s3_bucket" "api_truststore" {
  bucket        = "${local.prefix}--api-truststore"
  force_destroy = true
}

resource "aws_s3_bucket_policy" "api_truststore_bucket_policy" {
  bucket = aws_s3_bucket.api_truststore.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "api_truststore_bucket_policy"
    Statement = [
      {
        Sid       = "HTTPSOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.api_truststore.arn,
          "${aws_s3_bucket.api_truststore.arn}/*",
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

resource "aws_s3_bucket_public_access_block" "api-truststore-public-access-block" {
  bucket = aws_s3_bucket.api_truststore.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "api_truststore" {
  bucket = aws_s3_bucket.api_truststore.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "api_truststore" {
  bucket = aws_s3_bucket.api_truststore.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_object" "api_truststore" {
  bucket = aws_s3_bucket.api_truststore.bucket
  key    = "certificates.pem"
  source = "../../truststore/server/${var.account_name}.pem"
  etag   = filemd5("../../truststore/server/${var.account_name}.pem")
}
