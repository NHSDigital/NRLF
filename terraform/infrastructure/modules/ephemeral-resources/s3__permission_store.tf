resource "aws_s3_bucket" "authorization-store" {
  bucket        = "${var.prefix}--authorization-store"
  force_destroy = true

  tags = {
    Name        = "authorization store"
    Environment = "${var.prefix}"
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
