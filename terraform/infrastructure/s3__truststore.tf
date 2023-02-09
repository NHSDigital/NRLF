resource "aws_s3_bucket" "api_truststore" {
  bucket        = "${local.prefix}--api-truststore"
  force_destroy = true
}

resource "aws_s3_bucket_acl" "api_truststore" {
  bucket = aws_s3_bucket.api_truststore.id
  acl    = "private"
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
  source = "../../truststore/server/${local.account_name}.pem"
  etag   = filemd5("../../truststore/server/${local.account_name}.pem")
}
